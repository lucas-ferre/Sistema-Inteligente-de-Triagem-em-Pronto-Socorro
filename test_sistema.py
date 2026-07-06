"""Testes unitários do sistema de triagem.

Cobrem as três garantias centrais do trabalho:
  1. A rede bayesiana é válida (CPTs somam 1) e coerente clinicamente.
  2. A heurística do A* é admissível (nunca superestima o custo real).
  3. O A* encontra o ótimo global e nunca perde para FIFO ou Gulosa.

Executar com:
    python -m pytest test_sistema.py -v
"""

import itertools
import random

import pytest

from algoritmo_busca import (
    Paciente,
    EstadoBusca,
    executar_a_estrela,
    estrategia_fifo,
    estrategia_gulosa,
    calcular_risco_ordem_fixa,
    TEMPO_CONSULTA_MINUTOS,
)


def gerar_fila_aleatoria(quantidade: int, semente: int) -> list:
    """Fila sintética reprodutível, independente do CSV e da rede."""
    sorteio = random.Random(semente)
    return [
        Paciente(nome=f"P{i:02d}",
                 p_gravidade_alta=round(sorteio.uniform(0.05, 0.95), 2),
                 tempo_espera=sorteio.randint(5, 60))
        for i in range(quantidade)
    ]


def custo_otimo_forca_bruta(pacientes: list) -> float:
    """Menor risco acumulado dentre todas as ordens de atendimento."""
    return min(
        calcular_risco_ordem_fixa(list(permutacao), TEMPO_CONSULTA_MINUTOS)
        for permutacao in itertools.permutations(pacientes)
    )


# ---------------------------------------------------------------------------
# Módulo 1 — Rede Bayesiana
# ---------------------------------------------------------------------------

def test_rede_valida_e_cpts_somam_um():
    pytest.importorskip("pgmpy")
    from rede_bayesiana import construir_rede

    modelo = construir_rede()
    assert modelo.check_model()

    # Cada uma das 48 colunas da CPT de Gravidade deve somar exatamente 1
    somas_por_coluna = modelo.get_cpds('Gravidade').get_values().sum(axis=0)
    assert somas_por_coluna == pytest.approx(1.0)


def test_inferencia_coerente_clinicamente():
    pytest.importorskip("pgmpy")
    from rede_bayesiana import (
        obter_distribuicao_gravidade,
        obter_probabilidade_gravidade,
    )

    paciente_grave = {'Febre': 1, 'Saturacao_O2': 2, 'Idade_Doenca': 1,
                      'Pressao_Arterial': 1, 'Nivel_Dor': 1}
    paciente_saudavel = {sintoma: 0 for sintoma in paciente_grave}

    # A distribuição de saída é uma probabilidade válida
    distribuicao = obter_distribuicao_gravidade(paciente_grave)
    assert len(distribuicao) == 3
    assert sum(distribuicao) == pytest.approx(1.0)

    # Todos os sintomas no pior estado => P(alta) maior que sem sintomas
    assert (obter_probabilidade_gravidade(paciente_grave)
            > obter_probabilidade_gravidade(paciente_saudavel))


# ---------------------------------------------------------------------------
# Módulo 2 — Algoritmo A*
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("semente", range(5))
def test_heuristica_admissivel(semente):
    """h(n) do estado inicial nunca excede o custo ótimo real (h*)."""
    pacientes = gerar_fila_aleatoria(5, semente)
    estado_inicial = EstadoBusca(fila_espera=tuple(pacientes), atendidos=(),
                                 custo_g=0.0, tempo_decorrido=0.0)
    assert estado_inicial.calcular_h() <= custo_otimo_forca_bruta(pacientes) + 1e-9


@pytest.mark.parametrize("semente", range(5))
def test_a_estrela_encontra_otimo_global(semente):
    """O custo do A* iguala o mínimo exaustivo em filas pequenas."""
    pacientes = gerar_fila_aleatoria(5, semente)
    resultado = executar_a_estrela(pacientes)
    assert resultado.custo_g == pytest.approx(custo_otimo_forca_bruta(pacientes))


@pytest.mark.parametrize("semente", range(5))
def test_a_estrela_nunca_pior_que_fifo_e_gulosa(semente):
    pacientes = gerar_fila_aleatoria(8, semente)
    custo_a_estrela = executar_a_estrela(pacientes).custo_g
    custo_fifo = calcular_risco_ordem_fixa(estrategia_fifo(pacientes))
    custo_gulosa = calcular_risco_ordem_fixa(estrategia_gulosa(pacientes))
    assert custo_a_estrela <= custo_fifo + 1e-9
    assert custo_a_estrela <= custo_gulosa + 1e-9


def test_custo_do_a_estrela_consistente_com_simulacao_de_ordem_fixa():
    """custo_g do A* e calcular_risco_ordem_fixa medem a mesma coisa,
    garantindo que a comparação entre as três estratégias é justa."""
    pacientes = gerar_fila_aleatoria(5, semente=123)
    resultado = executar_a_estrela(pacientes)
    custo_simulado = calcular_risco_ordem_fixa(list(resultado.atendidos))
    assert resultado.custo_g == pytest.approx(custo_simulado)
