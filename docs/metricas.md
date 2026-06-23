# Métricas calculadas

## 1. Churn

**O que é:** volume total de linhas modificadas em um arquivo ao longo do tempo.

```
churn = linhas_adicionadas + linhas_removidas
```

Um churn alto indica que o arquivo está em constante mudança, o que pode
significar instabilidade do design ou requisitos em evolução frequente.

---

## 2. Complexidade Ciclomática

**O que é:** número de caminhos de execução independentes em uma função.
Calculada por **Lizard** sobre o estado atual dos arquivos.

| Valor | Interpretação |
|-------|--------------|
| 1–5 | Baixo risco, fácil de testar |
| 6–10 | Moderado — pode ser simplificado |
| 11–20 | Alto — difícil de testar completamente |
| > 20 | Muito alto — forte candidato a refatoração |

No Sauron, é armazenada como **média das funções** do arquivo em `FileMetrics.cyclomatic_complexity`.

---

## 3. Score de Hotspot

**O que é:** pontuação composta que combina frequência de mudanças com complexidade estática. Arquivos com score alto são candidatos prioritários para refatoração.

$$\text{score} = \ln(1 + \text{commits}) \times (1 + \overline{\text{complexidade}})$$

**Por que logaritmo no número de commits?**  
Um arquivo com 1000 commits não é 10× mais problemático que um com 100.
O crescimento logarítmico normaliza repositórios com históricos muito longos
e evita que a frequência de mudanças domine completamente o score.

**Exemplos:**

| Arquivo | Commits | Complexidade | Score |
|---------|---------|-------------|-------|
| `utils.py` | 5 | 2,0 | `ln(6) × 3,0 ≈ 5,4` |
| `engine.py` | 50 | 15,0 | `ln(51) × 16,0 ≈ 62,8` |
| `config.py` | 200 | 1,0 | `ln(201) × 2,0 ≈ 10,6` |
| `core.py` | 80 | 30,0 | `ln(81) × 31,0 ≈ 137,3` |

`core.py` é o hotspot mais crítico: alta frequência **e** alta complexidade.

---

## 4. Grau de Acoplamento Lógico

**O que é:** percentual dos commits de um arquivo que também tocaram outro arquivo específico.

O denominador usa o **mínimo** dos dois para normalizar pelo arquivo menos modificado.
Isso evita que um arquivo muito ativo dilua artificialmente o grau de acoplamento.

| Grau | Interpretação |
|------|--------------|
| > 0,8 | Acoplamento muito forte — os arquivos são quase inseparáveis |
| 0,5–0,8 | Acoplamento significativo — mudanças em A frequentemente exigem mudanças em B |
| 0,2–0,5 | Acoplamento moderado — vale investigar |
| < 0,2 | Acoplamento fraco — provavelmente coincidência |

Pares com menos de 2 co-mudanças são descartados para evitar ruído.

---

## 5. Detecção de God Class

**O que é:** identificação de arquivos que concentram responsabilidade demais,
tornando-se pontos únicos de falha e gargalos de manutenção.

Um arquivo é classificado como god class se satisfizer **qualquer** condição:

```
soma_complexidade_ciclomática ≥ complexity_threshold   (padrão: 50)
    OU
número_de_funções ≥ method_threshold                   (padrão: 20)
```

Os limiares são configuráveis via `--complexity-threshold` e `--method-threshold`.

---

## 6. Métricas de Issues (GitHub)

| Métrica | Cálculo |
|---------|---------|
| `total_open` | Contagem de issues abertas no momento da análise |
| `total_closed` | Contagem de issues fechadas |
| `avg_resolution_days` | Média de `(closed_at − created_at)` em dias para todas as issues fechadas |
| `long_running_count` | Issues abertas há mais de 90 dias (configurável internamente) |
| `reopened_count` | Issues que foram reabertas após fechamento |

Issues que são pull requests são excluídas dessa contagem (filtradas via `issue.pull_request is None`).

---

## 7. Métricas de Pull Requests (GitHub)

| Métrica | Cálculo |
|---------|---------|
| `total_open` | PRs abertos no momento da análise |
| `total_merged` | PRs que foram mergeados |
| `total_closed_unmerged` | PRs fechados **sem** merge (rejeitados) |
| `rejection_rate` | `closed_unmerged / (merged + closed_unmerged)` |
| `avg_review_time_days` | Média de `(merged_at − created_at)` em dias para PRs mergeados |
| `long_running_count` | PRs abertos há mais de 90 dias |

Uma `rejection_rate` alta pode indicar problemas no processo de revisão,
PRs muito grandes ou falta de alinhamento entre autor e revisores.

---

## 8. Métricas por Autor

| Métrica | Descrição |
|---------|-----------|
| `commit_count` | Total de commits do autor em todo o período analisado |
| `files_touched` | Soma de arquivos distintos modificados (pode contar o mesmo arquivo várias vezes) |
| `lines_added` | Total de linhas adicionadas pelo autor |
| `lines_removed` | Total de linhas removidas pelo autor |

> **Atenção:** `files_touched` conta ocorrências, não arquivos únicos.
> Um autor que modificou o mesmo arquivo 10 vezes terá `files_touched += 10`.
> Isso reflete o esforço de manutenção, não a amplitude do impacto.
