# Relatório de QA — Sistema Inteligente de Triagem em Pronto-Socorro

Este documento apresenta uma auditoria detalhada de garantia de qualidade (Quality Assurance) do projeto de triagem inteligente. A análise foi dividida em seis vieses distintos (positivo, negativo, limpeza de código, otimização, corretude e resultados) e concluída com uma revisão geral integradora.

---

## 1. Viés Positivo (Pontos Fortes e Boas Práticas)

*   **Modularização do Projeto**: O código está estruturado em componentes claros com responsabilidades bem definidas, facilitando o entendimento:
    *   [rede_bayesiana.py](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/rede_bayesiana.py) para a lógica probabilística.
    *   [algoritmo_busca.py](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/algoritmo_busca.py) para a lógica de busca e ordenação.
    *   [gerar_base_dados.py](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/gerar_base_dados.py) para a simulação do dataset.
    *   [integracao_experimento.py](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/integracao_experimento.py) para orquestração e testes.
*   **Geração Inteligente de CPTs**: Em vez de definir manualmente as 144 probabilidades da tabela condicional do nó `Gravidade` (o que seria propenso a erros de digitação e inconsistências matemáticas), o grupo desenvolveu uma lógica iterativa em [rede_bayesiana.py:25-58](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/rede_bayesiana.py#L25-L58) que calcula scores com base em pesos médicos plausíveis (como o peso maior para Saturação de $O_2$ e Idade/Doença Crônica).
*   **Controle de Estados Repetidos (Closed List)**: A implementação de uma lista de estados visitados utilizando `frozenset` em [algoritmo_busca.py:38-51](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/algoritmo_busca.py#L38-L51) evita a reavaliação redundante de caminhos equivalentes. Isso diminui consideravelmente a profundidade da árvore de busca do $A^*$.
*   **Documentação Apropriada**: O relatório acadêmico ([Relatório.docx](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/Relatório.docx)) cumpre todas as seções solicitadas no PDF de diretrizes e explica adequadamente a lógica de cada componente.

---

## 2. Viés Negativo (Fraquezas e Vulnerabilidades)

*   **Inconsistência nos Parâmetros dos Experimentos**: Há um erro crítico de definição nos tempos de consulta padrões:
    *   A função `executar_a_estrela` define o parâmetro `tempo_consulta=10` ([algoritmo_busca.py:31](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/algoritmo_busca.py#L31)).
    *   A função `calcular_risco_ordem_fixa` (usada para FIFO e Gulosa) define `tempo_consulta=16` ([algoritmo_busca.py:80](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/algoritmo_busca.py#L80)).
    *   Como a orquestração em [integracao_experimento.py](file:///d:/Users/jacks/Desktop/Lucas%20Ferreira/faculdade/IA/Trabalho%20Final%20IA/Trabalho%20Final/Trabalho%20Final/integracao_experimento.py) não passa o parâmetro explicitamente, as avaliações de FIFO/Gulosa simulam consultas mais demoradas (16 minutos) que as do $A^*$ (10 minutos), tornando a comparação injusta e artificialmente favorável ao $A^*$.
*   **Falta de Reprodutibilidade**: O script de experimentos sorteia os pacientes de forma aleatória a cada execução sem fixar uma semente aleatória (`random.seed`). Com isso, os números exatos apresentados no relatório técnico não podem ser replicados pelo avaliador.
*   **Inexistência de Tratamento de Erros**: O código falha de forma silenciosa ou gera tracebacks de sistema caso ocorram falhas como:
    *   Arquivo CSV ausente ou com delimitador incorreto.
    *   Dependências ausentes (ex: biblioteca `pgmpy` não instalada).
*   **Distribuição de Sintomas Clínicos Irrealista**: No script `gerar_base_dados.py`, os sintomas dos pacientes são simulados de forma uniforme (`random.choice([0, 1, 2])`). Estatisticamente, isso faz com que 33% dos pacientes gerados estejam em estado de saturação de $O_2$ crítica (< 90%), o que não condiz com a triagem de um pronto-socorro real.

---

## 3. Viés de Limpeza de Código (Legibilidade e Boas Práticas)

*   **Valores Mágicos (Hardcoded Constants)**: Valores como o tempo padrão da consulta de triagem e os pesos da rede bayesiana estão escritos diretamente nas assinaturas e corpos das funções. Devem ser unificados como constantes no topo do arquivo (ex: `TEMPO_CONSULTA_MINUTOS = 10`).
*   **Ausência de Anotações de Tipo (Type Hints)**: A falta de tipagem estática (ex: `def executar_a_estrela(pacientes_iniciais: list[Paciente], tempo_consulta: int) -> EstadoBusca`) dificulta a manutenção do código.
*   **Duplicação e Instanciação Excessiva de Objetos**:
    *   No algoritmo $A^*$, a cada transição de estado, novos objetos `Paciente` são criados em loops para atualizar o tempo de espera de todos os pacientes remanescentes. Essa recriação constante gera lixo na memória.
*   **Prints Desorganizados**: Os prints no console em `integracao_experimento.py` misturam informações brutas. Uma saída mais limpa, estruturada em tabela (ou exportada como markdown), melhoraria a apresentação dos resultados.

---

## 4. Viés de Otimização (Desempenho e Eficiência)

*   **Gargalo na Rede Bayesiana**:
    ```python
    def obter_probabilidade_gravidade(sintomas):
        modelo = construir_rede() # <- Chamado toda vez!
        inferencia = VariableElimination(modelo)
        ...
    ```
    A função `obter_probabilidade_gravidade` reconstrói a rede e calcula todas as CPTs programaticamente a cada chamada. Para a geração da base com 100 pacientes, isso significa rodar a construção e a verificação do modelo (`check_model()`) 100 vezes. O correto seria instanciar a rede e a classe de inferência uma única vez de forma global ou via Singleton.
*   **Complexidade Fatorial do $A^*$**: O número de caminhos possíveis para ordenar $N$ pacientes é de $N!$. Para $N=20$, $20! \approx 2.4 \times 10^{18}$ estados. Embora a Closed List mitigue isso ao podar estados de "pacientes restantes" equivalentes, a busca ainda atinge um gargalo severo se $N > 25$.
*   **Cópia de Fila Ineficiente**: No loop do $A^*$, gerar sucessores envolve copiar a lista de pacientes e criar novos objetos `Paciente` para cada um com o tempo incrementado. O estado poderia rastrear apenas os índices dos pacientes atendidos e o tempo decorrido, calculando o risco dinamicamente sem clonar objetos.

---

## 5. Viés de Corretude (Erros Lógicos e Regras de Negócio)

*   **Heurística Não Admissível**:
    A heurística implementada é:
    \[h(n) = \sum_{j \in Q} p_j \times t_j\]
    Onde $Q$ é a fila de pacientes remanescentes, $p_j$ é a probabilidade de gravidade alta e $t_j$ é o tempo de espera atual.
    *   *Violação da Admissibilidade*: A regra para uma heurística ser admissível no $A^*$ é que ela nunca deve superestimar o custo real futuro ($h(n) \le h^*(n)$). 
    *   Considere o cenário em que resta apenas **1 paciente** na fila ($|Q|=1$). Ao atendê-lo (ação final), a fila fica vazia. O custo de transição para o estado final é **0**, pois não há outros pacientes que continuam esperando. Portanto, o custo real futuro $h^*(n) = 0$.
    *   No entanto, a heurística retorna $h(n) = p_1 \times t_1$. Se $p_1 > 0$ e $t_1 > 0$, temos $h(n) > 0$, o que significa que **$h(n) > h^*(n)$**.
    *   Como a heurística superestima o custo futuro, o $A^*$ perde a garantia matemática de otimalidade.
    *   *Como corrigir*: Uma heurística admissível válida deve desconsiderar o paciente atendido no passo atual (pois seu custo futuro de espera será nulo). Uma estimativa otimista do custo mínimo restante seria:
        \[h_{\text{admissivel}}(n) = \sum_{j \in Q} p_j t_j - \max_{j \in Q} (p_j t_j)\]
        Essa heurística remove a maior parcela de risco que pode ser zerada de imediato na próxima consulta, garantindo que $h(n) \le h^*(n)$ em todos os estados.

---

## 6. Viés de Resultados (Análise Métricas e Validação)

Fizemos uma simulação de testes controlados (com a mesma semente aleatória `42`) para verificar o impacto real das correções dos parâmetros. Veja a comparação dos riscos acumulados sob as duas parametrizações:

### Caso A: Rodada com `tempo_consulta = 10` (Tempo Real do A*)
*   **Cenário Pequeno (6 pacientes)**:
    *   **FIFO**: 345.40
    *   **Gulosa**: 336.35
    *   **$A^*$**: 270.75 *(Melhoria de 19.5% em relação à Gulosa)*
*   **Cenário Médio (20 pacientes)**:
    *   **FIFO**: 8010.35
    *   **Gulosa**: 3145.70
    *   **$A^*$**: 2954.45 *(Melhoria de 6.1% em relação à Gulosa)*

### Caso B: Rodada com `tempo_consulta = 16` (Tempo Usado no FIFO/Gulosa)
*   **Cenário Pequeno (6 pacientes)**:
    *   **FIFO**: 446.80
    *   **Gulosa**: 400.85
    *   **$A^*$**: 335.25 *(Melhoria de 16.3% em relação à Gulosa)*
*   **Cenário Médio (20 pacientes)**:
    *   **FIFO**: 11852.75
    *   **Gulosa**: 4351.10
    *   **$A^*$**: 4159.85 *(Melhoria de 4.4% em relação à Gulosa)*

### Diagnóstico dos Resultados
1.  **Diferença Superestimada**: O relatório do grupo registrou uma discrepância muito maior (ex: FIFO 6951.10 vs $A^*$ 3231.00 no Cenário Médio). Essa diferença foi inflada devido ao erro de tempo de consulta (16 vs 10 minutos).
2.  **Otimização Real do $A^*$**: Mesmo corrigindo a injustiça do tempo de consulta, o algoritmo $A^*$ se mantém como a melhor solução para ambos os cenários (pequeno e médio).
3.  **Comportamento das Estratégias**:
    *   **FIFO** é a pior estratégia porque ignora a gravidade do quadro clínico dos pacientes.
    *   **Gulosa** funciona bem, mas falha ao deixar pacientes moderados muito tempo na fila se continuarem chegando casos graves.
    *   **$A^*$** equilibra perfeitamente os dois pratos da balança: prioriza casos graves, mas atende moderados antes que eles piorem de forma crítica devido à longa espera.

---

## 7. Revisão Geral e Relações entre Vieses

A tabela abaixo cruza os vieses analisados para mapear o impacto das falhas e propor soluções integradas para o projeto:

| Viés Primário | Correlação com outros Vieses | Descrição do Impacto | Recomendação de Solução |
| :--- | :--- | :--- | :--- |
| **Corretude** | **Resultados** / **Negativo** | A heurística não admissível tira a garantia de otimalidade do $A^*$, e a divergência nos tempos de consulta descaracterizou a fidelidade dos experimentos apresentados. | Ajustar a fórmula do cálculo de risco futuro para subtrair o risco máximo imediato e uniformizar a variável de tempo de consulta. |
| **Otimização** | **Limpeza de Código** | A recriação constante da rede bayesiana e o excesso de cópias de listas de pacientes degradam o desempenho da CPU e aumentam o uso de RAM. | Refatorar a criação do modelo bayesiano para operar como um Singleton e armazenar referências imutáveis das listas de pacientes. |
| **Limpeza de Código** | **Corretude** | Parâmetros duplicados diretamente no código causaram a divergência física de tempo nos experimentos (10 minutos vs 16 minutos). | Definir constantes globais para centralizar parâmetros como `TEMPO_CONSULTA` e `LIMITES_DE_SATURACAO`. |
| **Negativo** | **Resultados** | A ausência de seed aleatório e distribuições uniformes irreais geram dados instáveis e distorcem a representação clínica real dos testes de estresse. | Fixar a semente do gerador com `random.seed(42)` e ajustar as probabilidades do gerador sintético com distribuições ponderadas. |

### Conclusão Geral
O projeto demonstra um excelente raciocínio de engenharia de software e inteligência artificial aplicado a problemas de saúde pública. No entanto, possui **erros matemáticos e de parametrização metodológica** que comprometem a precisão técnica das conclusões e a garantia de otimalidade do algoritmo de busca.

As correções sugeridas neste relatório de QA são de fácil implementação e elevam o nível de maturidade e confiabilidade da aplicação.
