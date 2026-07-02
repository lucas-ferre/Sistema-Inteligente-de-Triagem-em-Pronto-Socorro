# Sistema Inteligente de Triagem em Pronto-Socorro

Trabalho final da disciplina de CK0248 - Inteligência Artificial.
Ministrada pelo Docente - Jose Antonio Fernandes de Macedo.

---

Equipe Formada por:

1.  Antonio Irineu Filho | 509916
2.  Lucas Ferreira da Silva | 567414

---

O sistema resolve dois subproblemas complementares e integrados:

1. **Rede Bayesiana** — estima a probabilidade de gravidade (baixa/média/alta)
   de cada paciente a partir de 5 variáveis clínicas: Febre, Saturação de O₂,
   Pressão Arterial, Nível de Dor e Idade + Doença Crônica.
2. **Algoritmo A\*** — decide a melhor ordem de atendimento minimizando o
   risco acumulado, onde `risco(paciente) = P(gravidade_alta) × tempo_esperando`.

A integração é direta: a probabilidade `P(Gravidade = alta)` produzida pela
rede bayesiana alimenta a função de custo e a heurística do A\*.

## Estrutura do projeto

| Arquivo | Descrição |
| --- | --- |
| `rede_bayesiana.py` | Módulo 1 — estrutura da rede, CPTs geradas programaticamente e inferência (pgmpy) |
| `algoritmo_busca.py` | Módulo 2 — A\* com heurística admissível, closed list e estratégias FIFO/Gulosa |
| `gerar_base_dados.py` | Gera a base simulada de 100 pacientes (distribuições ponderadas realistas) |
| `integracao_experimento.py` | Orquestra os experimentos comparando FIFO × Gulosa × A\* |
| `base_pacientes_simulados.csv` | Base simulada gerada (delimitador `;`) |

## Requisitos

- Python 3.10+
- [pgmpy](https://pgmpy.org/)

```bash
pip install pgmpy
```

## Como executar

```bash
# 1. (Opcional) Regenerar a base simulada de pacientes
python gerar_base_dados.py

# 2. Rodar os experimentos comparativos (cenário pequeno e médio)
python integracao_experimento.py
```

## Reprodutibilidade

Todos os sorteios usam semente aleatória fixa (`42`), tanto na geração da
base quanto na seleção de pacientes dos cenários — os números reportados no
relatório podem ser replicados executando os scripts acima.

## Experimentos

Três estratégias são comparadas sob o **mesmo tempo de consulta (10 min)**:

| Estratégia | Descrição |
| --- | --- |
| FIFO | Atende na ordem de chegada, ignora gravidade |
| Gulosa | Atende sempre o de maior P(gravidade alta), ignora tempo de espera |
| A\* | Minimiza o risco acumulado total considerando gravidade **e** tempo |

Resultados (semente 42, consulta de 10 min):

| Cenário | FIFO | Gulosa | A\* |
| --- | ---: | ---: | ---: |
| Pequeno (6 pacientes) | 147.10 | 55.55 | **48.35** |
| Médio (20 pacientes) | 5861.45 | 1752.75 | **1722.40** |

O A\* produz o menor risco acumulado nos dois cenários, como esperado. No
cenário pequeno, a otimalidade foi verificada por força bruta (720 permutações).

## Notas de modelagem

- **Heurística admissível**: `h(n) = Σ riscos atuais − max(risco atual)`.
  A soma pura superestimaria o custo real (com 1 paciente restante o custo
  futuro é 0), o que quebraria a garantia de otimalidade do A\*.
- **CPTs**: os valores foram estimados de forma plausível (declarado no
  relatório), com pesos maiores para Saturação de O₂ e Idade/Doença Crônica,
  inspirados no Protocolo de Manchester.
- **Base simulada**: os sintomas seguem distribuições ponderadas coerentes com
  as CPTs a priori da rede (ex.: ~10% de saturação crítica, não 33%).
# Sistema-Inteligente-de-Triagem-em-Pronto-Socorro
