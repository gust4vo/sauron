# Arquitetura

## Visão geral

O Sauron segue uma arquitetura em pipeline linear com três camadas bem separadas:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI  (main.py)                           │
│  Recebe argumentos · orquestra etapas · exibe progresso         │
└────────────┬──────────────────────────────────────┬────────────┘
             │                                      │
     ┌───────▼────────┐                    ┌────────▼────────┐
     │   ANALYZERS    │                    │    REPORTERS    │
     │                │                    │                 │
     │ git_analyzer   │                    │ terminal_reporter│
     │ code_analyzer  │                    │ file_reporter   │
     │ github_analyzer│                    └─────────────────┘
     │ hotspot_detector                              ▲
     └───────┬────────┘                             │
             │                                      │
     ┌───────▼────────────────────────────────────┐ │
     │                 MODELS                     │─┘
     │  FileMetrics · Hotspot · LogicalCoupling   │
     │  AuthorMetrics · IssueMetrics · PRMetrics  │
     │  AnalysisResult                            │
     └────────────────────────────────────────────┘
```

Os **analyzers** produzem modelos de dados. Os **reporters** consomem modelos de dados.
Nenhum analyzer conhece nenhum reporter — o acoplamento passa sempre pelos modelos.

---

## Estrutura de arquivos

```
sauron/
├── pyproject.toml               ← configuração do pacote e dependências
├── .gitignore
│
├── sauron/                      ← pacote Python principal
│   ├── __init__.py              ← exporta __version__
│   ├── main.py                  ← CLI (Typer) — ponto de entrada `sauron`
│   ├── models.py                ← dataclasses de todos os tipos de resultado
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── git_analyzer.py      ← histórico Git (PyDriller)
│   │   ├── code_analyzer.py     ← análise estática (Lizard)
│   │   ├── github_analyzer.py   ← issues e PRs (PyGithub)
│   │   └── hotspot_detector.py  ← pontuação e ranking
│   │
│   └── reporters/
│       ├── __init__.py
│       ├── terminal_reporter.py ← tabelas Rich
│       └── file_reporter.py     ← exportação CSV e JSON
│
├── tests/
│   ├── __init__.py
│   └── test_analyzers.py        ← testes unitários
│
└── docs/                        ← esta documentação
```

---

## Fluxo de execução detalhado

```
sauron analyze <repo> [opções]
        │
        ▼
 1. Validar --since (formato YYYY-MM-DD)
        │
        ▼
 2. É URL remota?
    ├── Sim → GitPython clona para diretório temporário em /tmp/sauron_XXXXX/
    └── Não → usa o caminho local diretamente
        │
        ▼
 3. analyze_git_history(local_path, since?)
    ├── PyDriller itera cada commit em ordem cronológica
    ├── Para cada commit:
    │   ├── Acumula métricas de autor (commit_count, lines_added, ...)
    │   └── Para cada arquivo modificado:
    │       └── Acumula FileMetrics (commit_count, churn, authors, ...)
    ├── Após todos os commits:
    │   └── Conta pares co-modificados → calcula coupling_degree
    └── Retorna: file_metrics, logical_couplings, author_metrics
        │
        ▼
 4. analyze_code_metrics(local_path, file_metrics)  ← se não --no-code
    ├── Para cada arquivo em file_metrics:
    │   ├── Lizard analisa o arquivo no disco
    │   └── Atualiza FileMetrics com complexity, function_count, ...
    └── Retorna lista de god_classes
        │
        ▼
 5. detect_hotspots(file_metrics, top_n)
    ├── Calcula score = log(1+commits) × (1+complexity) para cada arquivo
    └── Retorna top_n ordenados por score decrescente
        │
        ▼
 6. analyze_github(repo_url, token?)  ← se não --no-github e URL remota
    ├── PyGithub autentica e busca issues (state=all)
    ├── Filtra PRs da lista de issues
    ├── Calcula avg_resolution_days, long_running_count
    ├── Busca PRs separadamente
    └── Retorna IssueMetrics, PRMetrics
        │
        ▼
 7. Montar AnalysisResult
        │
        ▼
 8. Saída conforme --output:
    ├── terminal → print_analysis() com Rich
    ├── csv      → export_csv() — um CSV por categoria
    └── json     → export_json() — único arquivo
        │
        ▼
 9. Limpar diretório temporário (se clonagem remota)
```

---

## Módulo a módulo

### `sauron/main.py`

Responsável por:
- Declarar o app Typer e todos os comandos (`analyze`, `version`)
- Validar entradas do usuário (`--since`, existência do path)
- Gerenciar o ciclo de vida do clone temporário com `try/finally` implícito
- Exibir o spinner de progresso via `rich.progress.Progress`
- Montar o `AnalysisResult` final e despachar para o reporter correto

Não contém lógica de análise — delega tudo para os analyzers.

---

### `sauron/models.py`

Define os contratos de dados entre analyzers e reporters usando `@dataclass`.
Nenhuma lógica de negócio — apenas campos tipados.

Hierarquia de modelos:

```
AnalysisResult
├── list[FileMetrics]       ← um por arquivo único no histórico
├── list[Hotspot]           ← subconjunto de FileMetrics com score
├── list[LogicalCoupling]   ← pares de arquivos co-modificados
├── list[AuthorMetrics]     ← um por e-mail/autor único
├── IssueMetrics | None     ← agregado de todas as issues
└── PRMetrics | None        ← agregado de todos os PRs
```

---

### `sauron/analyzers/git_analyzer.py`

Usa **PyDriller** para iterar os commits em ordem cronológica.

Pontos de atenção na implementação:
- `mod.new_path or mod.old_path` — trata renomeações de arquivo sem perder o histórico
- O acoplamento lógico só considera pares com `count >= 2` para evitar ruído
- `author_key = email or name` — fallback para autores sem e-mail configurado

---

### `sauron/analyzers/code_analyzer.py`

Usa **Lizard** que suporta mais de 20 linguagens (Python, Java, C/C++, Go, JS, etc.)
sem necessidade de compilador ou ambiente de execução da linguagem alvo.

A análise é feita sobre os arquivos **no estado atual do disco**, não sobre
cada versão histórica — isso é uma escolha de performance consciente.

Critério de god class (OR lógico):
```
total_complexity >= complexity_threshold   (padrão: 50)
    OU
len(functions)   >= method_threshold       (padrão: 20)
```

---

### `sauron/analyzers/github_analyzer.py`

A função `_extract_repo_name` usa regex para aceitar:
- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `git@github.com:owner/repo.git`

Retorna `None` para URLs que não são do GitHub (GitLab, Bitbucket, etc.),
fazendo a análise ser silenciosamente ignorada.

A paginação é limitada por `max_items=1000` por padrão para evitar
timeout em repositórios com histórico muito longo de issues.

---

### `sauron/analyzers/hotspot_detector.py`

Fórmula do score documentada em [docs/metricas.md](metricas.md).

A função é pura (sem efeitos colaterais) e testável de forma isolada.

---

### `sauron/reporters/terminal_reporter.py`

Cada seção do relatório é uma função privada `_print_*` chamada pelo
`print_analysis` principal. Adicionar uma nova seção é simplesmente
criar `_print_nova_secao(result)` e chamá-la.

---

### `sauron/reporters/file_reporter.py`

- **CSV**: um arquivo por categoria, nomeados com timestamp para não sobrescrever execuções anteriores.
- **JSON**: arquivo único com todos os dados aninhados, compatível com qualquer ferramenta de análise downstream.

---

## Decisões de design

| Decisão | Alternativa considerada | Motivo da escolha |
|---------|------------------------|-------------------|
| Dataclasses para modelos | Pydantic | Sem dependência externa; simples para o escopo do projeto |
| PyDriller para Git | GitPython direto | API de alto nível mais legível; menos código de parsing manual |
| Lizard para complexidade | radon | Multi-linguagem; funciona sem instalar o runtime da linguagem |
| Typer para CLI | Click, argparse | Inferência de tipos automática; help gerado automaticamente |
| Clone em `/tmp` e limpeza posterior | Manter o clone | Evita acúmulo de repositórios em disco |
| Limite `max_items=1000` na API GitHub | Buscar tudo | Evita timeout e esgotamento de rate limit em repos grandes |
