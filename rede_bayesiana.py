"""Módulo 1 — Rede Bayesiana.

Estima a probabilidade de gravidade de um paciente a partir dos sintomas e
sinais vitais. A saída P(Gravidade = alta) alimenta a função de custo do A*.
"""

import itertools

try:
    from pgmpy.models import DiscreteBayesianNetwork
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.inference import VariableElimination
except ImportError as erro:
    raise ImportError(
        "A biblioteca 'pgmpy' não está instalada. "
        "Instale com: pip install pgmpy"
    ) from erro

# Pesos médicos plausíveis de cada sintoma no score de gravidade.
# Saturação de O2 crítica e idade avançada/doença crônica pesam mais.
PESOS_SINTOMAS = {
    'Febre': 1.0,
    'Saturacao_O2': 2.0,
    'Idade_Doenca': 1.5,
    'Pressao_Arterial': 1.0,
    'Nivel_Dor': 0.5,
}

# Dois limiares dividem o score em três faixas de gravidade:
#   score abaixo do primeiro  -> perfil de gravidade baixa
#   score entre os dois       -> perfil de gravidade média
#   score acima do segundo    -> perfil de gravidade alta
LIMIAR_SCORE_BAIXA_MEDIA = 2.5  # fronteira entre gravidade baixa e média
LIMIAR_SCORE_MEDIA_ALTA = 4.5   # fronteira entre gravidade média e alta


def construir_rede() -> DiscreteBayesianNetwork:
    # 1. Estrutura com 5 variáveis de entrada convergindo para Gravidade
    modelo = DiscreteBayesianNetwork([
        ('Febre', 'Gravidade'),
        ('Saturacao_O2', 'Gravidade'),
        ('Idade_Doenca', 'Gravidade'),
        ('Pressao_Arterial', 'Gravidade'),
        ('Nivel_Dor', 'Gravidade')
    ])

    # 2. CPTs dos Sintomas (Pais)
    cpd_febre = TabularCPD(variable='Febre', variable_card=2, values=[[0.6], [0.4]])
    cpd_saturacao = TabularCPD(variable='Saturacao_O2', variable_card=3, values=[[0.7], [0.2], [0.1]])
    cpd_idade = TabularCPD(variable='Idade_Doenca', variable_card=2, values=[[0.5], [0.5]])

    # 0 = Normal/Leve, 1 = Alterada/Intensa
    cpd_pressao = TabularCPD(variable='Pressao_Arterial', variable_card=2, values=[[0.7], [0.3]])
    cpd_dor = TabularCPD(variable='Nivel_Dor', variable_card=2, values=[[0.6], [0.4]])

    # 3. Gerando as 48 combinações de Gravidade programaticamente
    valores_baixa = []
    valores_media = []
    valores_alta = []

    # Iterando sobre todas as combinações: Febre, Sat, Idade, Pressao, Dor
    for f, s, i, p, d in itertools.product([0, 1], [0, 1, 2], [0, 1], [0, 1], [0, 1]):

        # Heurística: calculando um "peso" para os sintomas apresentados
        score = (f * PESOS_SINTOMAS['Febre']
                 + s * PESOS_SINTOMAS['Saturacao_O2']
                 + i * PESOS_SINTOMAS['Idade_Doenca']
                 + p * PESOS_SINTOMAS['Pressao_Arterial']
                 + d * PESOS_SINTOMAS['Nivel_Dor'])

        # Distribuindo probabilidades baseadas no score
        if score < LIMIAR_SCORE_BAIXA_MEDIA:
            valores_baixa.append(0.80)
            valores_media.append(0.15)
            valores_alta.append(0.05)
        elif score < LIMIAR_SCORE_MEDIA_ALTA:
            valores_baixa.append(0.20)
            valores_media.append(0.60)
            valores_alta.append(0.20)
        else:
            valores_baixa.append(0.05)
            valores_media.append(0.15)
            valores_alta.append(0.80)

    # 4. CPT da Gravidade (Nó Filho)
    cpd_gravidade = TabularCPD(
        variable='Gravidade',
        variable_card=3,
        evidence=['Febre', 'Saturacao_O2', 'Idade_Doenca', 'Pressao_Arterial', 'Nivel_Dor'],
        evidence_card=[2, 3, 2, 2, 2],
        values=[valores_baixa, valores_media, valores_alta]
    )

    modelo.add_cpds(cpd_febre, cpd_saturacao, cpd_idade, cpd_pressao, cpd_dor, cpd_gravidade)

    # Valida se as probabilidades foram geradas corretamente (somam 1)
    assert modelo.check_model()
    return modelo

_motor_inferencia: VariableElimination = None


def _obter_motor_inferencia() -> VariableElimination:
    global _motor_inferencia
    if _motor_inferencia is None:
        _motor_inferencia = VariableElimination(construir_rede())
    return _motor_inferencia


def obter_distribuicao_gravidade(sintomas: dict) -> list:
    """Retorna a distribuição completa [P(baixa), P(média), P(alta)]."""
    probabilidades = _obter_motor_inferencia().query(
        variables=['Gravidade'],
        evidence=sintomas
    )
    return list(probabilidades.values)


def obter_probabilidade_gravidade(sintomas: dict) -> float:
    return obter_distribuicao_gravidade(sintomas)[2]  # P(Gravidade = Alta)
