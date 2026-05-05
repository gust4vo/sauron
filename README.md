# TP1 — Mineração de Repositórios de Software

Trabalho prático da disciplina **Engenharia de Software 2** (UFMG, 2026/1). O objetivo é desenvolver uma ferramenta de linha de comando que identifique problemas de manutenção de software por meio da mineração de repositórios.

Referência: [andrehora/software-repo-mining](https://github.com/andrehora/software-repo-mining/blob/main/README.md).

## 1. Membros do grupo

- Gustavo Henrique Silva Paiva
- Luis Antonio Duarte Sousa
- Marcus Vinicius Moraes Oliveira
- Luiz Felipe Lima Costa

## 2. Explicação do sistema

A ferramenta será uma aplicação de linha de comando (CLI) que recebe como entrada um repositório Git (local ou hospedado no GitHub) e produz um relatório com indicadores de problemas de manutenção encontrados na sua história.

A análise combina dados extraídos de diferentes artefatos do repositório:

- **Histórico de commits** — frequência de mudanças, autores, churn (linhas adicionadas/removidas) e arquivos modificados em conjunto.
- **Código-fonte** — métricas estáticas como complexidade ciclomática, tamanho de funções/classes, duplicação e *code smells*.
- **Issues e pull requests** — tempo de resolução, taxa de PRs rejeitados, discussões longas e issues reabertas.
- **CI/CD e testes** — falhas recorrentes em builds, cobertura e arquivos sem testes associados.

A partir desses dados, a ferramenta deve sinalizar sintomas como *hotspots* (arquivos modificados com muita frequência e alta complexidade), *god classes*, acoplamento lógico entre arquivos, módulos sem manutenção e gargalos de revisão. A saída pode ser apresentada como tabelas no terminal, arquivos CSV/JSON e visualizações gráficas.

O fluxo previsto é:

1. O usuário invoca a CLI passando a URL ou caminho do repositório e os tipos de análise desejados.
2. A ferramenta clona/abre o repositório e percorre seu histórico.
3. Métricas são calculadas e correlacionadas para identificar padrões de problemas de manutenção.
4. Um relatório é gerado, destacando os pontos críticos para o desenvolvedor priorizar.

## 3. Possíveis tecnologias utilizadas

A linguagem principal pretendida é **Python**, pelo ecossistema maduro de mineração de software. As opções em estudo:

**Linguagem e CLI**
- Python 3.11+
- [Typer](https://typer.tiangolo.com/) ou [Click](https://click.palletsprojects.com/) — construção da interface de linha de comando
- [Rich](https://rich.readthedocs.io/) — formatação de saída no terminal

**Mineração de repositórios Git**
- [PyDriller](https://pydriller.readthedocs.io/) — análise de commits, autores e mudanças por arquivo
- [GitPython](https://gitpython.readthedocs.io/) — acesso de baixo nível ao histórico Git

**Integração com GitHub**
- [PyGithub](https://pygithub.readthedocs.io/) — acesso a issues, pull requests e metadados via API REST do GitHub

**Métricas de código e qualidade**
- [Lizard](https://github.com/terryyin/lizard) — complexidade ciclomática multi-linguagem
- [Radon](https://radon.readthedocs.io/) — métricas para código Python
- [cloc](https://github.com/AlDanial/cloc) — contagem de linhas por linguagem
- [flake8](https://flake8.pycqa.org/) / [pylint](https://pylint.pycqa.org/) — *code smells* em Python

**Análise sintática e refatorações**
- [tree-sitter](https://tree-sitter.github.io/tree-sitter/) — parsing de múltiplas linguagens
- [RefactoringMiner](https://github.com/tsantalis/RefactoringMiner) — detecção de refatorações no histórico

**Visualização e relatórios**
- [pandas](https://pandas.pydata.org/) — manipulação de dados tabulares
- [matplotlib](https://matplotlib.org/) / [plotly](https://plotly.com/python/) — gráficos
- Exportação para CSV, JSON e Markdown

**Testes e empacotamento**
- [pytest](https://docs.pytest.org/) — testes automatizados
- [Poetry](https://python-poetry.org/) ou `pip` + `pyproject.toml` — gerenciamento de dependências
