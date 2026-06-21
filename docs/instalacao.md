# Instalação

## Pré-requisitos

| Requisito | Versão mínima | Verificação |
|-----------|--------------|-------------|
| Python | 3.11 | `python --version` |
| pip | qualquer | `pip --version` |
| git | qualquer | `git --version` |

O `git` precisa estar disponível no `PATH` do sistema pois a ferramenta o usa para clonar repositórios remotos.

---

## Instalação rápida

```bash
# 1. Clone o repositório
git clone <url-deste-repositorio>
cd sauron

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Instale o pacote com todas as dependências
pip install -e ".[dev]"

# 4. Verifique
sauron version
```

---

## Instalação somente de produção (sem ferramentas de desenvolvimento)

```bash
pip install -e .
```

---

## Dependências instaladas

### Produção

| Pacote | Versão mínima | Finalidade |
|--------|--------------|------------|
| `typer` | 0.12 | Interface de linha de comando |
| `rich` | 13 | Saída colorida e tabelas no terminal |
| `pydriller` | 2.6 | Mineração do histórico Git |
| `gitpython` | 3.1 | Clonagem de repositórios remotos |
| `PyGithub` | 2.3 | Acesso à API REST do GitHub |
| `lizard` | 1.17 | Complexidade ciclomática multi-linguagem |
| `radon` | 6 | Métricas adicionais para código Python |
| `pandas` | 2.2 | Manipulação de dados tabulares |
| `matplotlib` | 3.8 | Geração de gráficos |

### Desenvolvimento (`.[dev]`)

| Pacote | Finalidade |
|--------|------------|
| `pytest` | Execução dos testes |
| `pytest-cov` | Relatório de cobertura |
| `ruff` | Linter e formatador de código |

---

## Verificando a instalação

```bash
# Deve imprimir "sauron 0.1.0"
sauron version

# Deve exibir o help completo
sauron --help

# Teste rápido sem acesso à internet (repositório local)
sauron analyze /caminho/para/qualquer/repo/git --no-github
```

---

## Problemas comuns

### `sauron: command not found`
O ambiente virtual não está ativado ou o pacote não foi instalado.
```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

### `git clone` falha com erro de SSL
Configure o certificado do sistema ou passe a flag `GIT_SSL_NO_VERIFY=1` (apenas em ambientes de teste):
```bash
GIT_SSL_NO_VERIFY=1 sauron analyze https://github.com/owner/repo
```

### Erro de autenticação no GitHub
A análise de issues e PRs requer um token para repositórios privados e evita o limite de taxa da API para repositórios públicos.  
Consulte [docs/github_token.md](github_token.md) para criar e configurar um token.
