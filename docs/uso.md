# Guia de Uso

## Sintaxe geral

```
sauron analyze REPO [OPÇÕES]
```

`REPO` pode ser:
- URL de um repositório GitHub: `https://github.com/owner/repo`
- Caminho absoluto ou relativo para um repositório Git local: `/home/user/meu-projeto`

---

## Exemplos por caso de uso

### Análise básica de um repositório público

```bash
sauron analyze https://github.com/pallets/flask
```

Clona o repositório, analisa todo o histórico Git e exibe tabelas no terminal
com hotspots, acoplamentos lógicos, autores e métricas do GitHub.

---

### Análise de repositório local

```bash
sauron analyze /home/user/meu-projeto
```

Não clona nada — usa o repositório diretamente. Ideal para projetos privados
ou quando você não quer esperar pelo clone.

---

### Restringir o período analisado

```bash
# Somente commits a partir de 1º de janeiro de 2025
sauron analyze https://github.com/django/django --since 2025-01-01
```

Útil para focar em problemas recentes e ignorar dívida técnica histórica.

---

### Aumentar o número de resultados exibidos

```bash
# Mostrar top 20 em vez do padrão top 10
sauron analyze https://github.com/pallets/flask --top 20
```

---

### Análise com token GitHub (recomendado)

Sem token, a API do GitHub limita a 60 requisições/hora.  
Com token autenticado, o limite sobe para 5.000/hora.

```bash
# Opção 1: variável de ambiente (recomendado — não aparece no histórico do shell)
export GITHUB_TOKEN=ghp_SeuTokenAqui
sauron analyze https://github.com/owner/repo

# Opção 2: flag direta
sauron analyze https://github.com/owner/repo --github-token ghp_SeuTokenAqui
```

Consulte [docs/github_token.md](github_token.md) para criar um token.

---

### Análise rápida (sem GitHub, sem código)

```bash
sauron analyze https://github.com/pallets/flask --no-github --no-code
```

Pula a chamada à API do GitHub e a análise de complexidade com Lizard.
Útil quando você quer apenas as métricas de histórico Git rapidamente.

---

### Pular o acoplamento lógico

```bash
sauron analyze /meu/repo --no-coupling
```

O cálculo de acoplamento lógico pode ser lento em repositórios com muitos
arquivos por commit. Use `--no-coupling` para omiti-lo.

---

### Ajustar limiares de god class

```bash
# Arquivo com complexidade total >= 30 OU >= 15 funções é god class
sauron analyze /meu/repo --complexity-threshold 30 --method-threshold 15
```

Os padrões são `50` e `20` respectivamente. Ajuste conforme o perfil do projeto.

---

## Opções de saída

### Terminal (padrão)

```bash
sauron analyze https://github.com/pallets/flask
# ou explicitamente:
sauron analyze https://github.com/pallets/flask --output terminal
```

Exibe tabelas Rich coloridas diretamente no terminal.

---

### Exportar CSVs

```bash
sauron analyze https://github.com/pallets/flask --output csv --output-dir ./relatorios
```

Gera arquivos separados por categoria:

```
relatorios/
├── sauron_20260621_143022_hotspots.csv
├── sauron_20260621_143022_coupling.csv
├── sauron_20260621_143022_authors.csv
└── sauron_20260621_143022_god_classes.csv
```

---

### Exportar JSON

```bash
sauron analyze https://github.com/pallets/flask --output json --output-dir ./relatorios
```

Gera um único arquivo com todos os dados estruturados:

```
relatorios/
└── sauron_20260621_143022_report.json
```

Veja [docs/formatos_saida.md](formatos_saida.md) para a estrutura completa do JSON.

---

## Combinando opções

```bash
# Repositório privado, período restrito, top 25, exportar JSON
sauron analyze https://github.com/org/repo-privado \
  --github-token ghp_SeuToken \
  --since 2025-06-01 \
  --top 25 \
  --output json \
  --output-dir ./relatorios
```

---

## Referência rápida de flags

| Flag | Atalho | Padrão | Descrição |
|------|--------|--------|-----------|
| `--github-token` | `-t` | `$GITHUB_TOKEN` | Token pessoal do GitHub |
| `--output` | `-o` | `terminal` | Formato: `terminal`, `csv`, `json` |
| `--output-dir` | `-d` | `.` | Diretório para arquivos exportados |
| `--since` | — | — | Data de início `YYYY-MM-DD` |
| `--top` | `-n` | `10` | Itens exibidos por categoria |
| `--no-github` | — | `false` | Pular análise de issues/PRs |
| `--no-code` | — | `false` | Pular análise de complexidade |
| `--no-coupling` | — | `false` | Pular acoplamento lógico |
| `--complexity-threshold` | — | `50` | Limiar de complexidade para god class |
| `--method-threshold` | — | `20` | Limiar de métodos para god class |
| `--help` | — | — | Exibir ajuda |
