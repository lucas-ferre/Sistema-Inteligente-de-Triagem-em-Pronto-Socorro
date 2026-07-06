"""Verificação de otimalidade do A* por força bruta.

Reproduz o Cenário Pequeno dos experimentos (mesma semente aleatória) e
compara o risco acumulado encontrado pelo A* com o de TODAS as ordens de
atendimento possíveis (6 pacientes -> 6! = 720 permutações). Se alguma
permutação produzir risco menor que o do A*, a modelagem está errada.

Executar com:
    python verificar_otimalidade.py
"""

import itertools
import math
import random
import sys

from algoritmo_busca import (
    executar_a_estrela,
    calcular_risco_ordem_fixa,
    TEMPO_CONSULTA_MINUTOS,
)
from integracao_experimento import carregar_pacientes_do_csv, SEMENTE_ALEATORIA

# Mesmo tamanho do Cenário Pequeno de integracao_experimento.py — acima de
# ~8 pacientes a enumeração fatorial deixa de ser viável (10! = 3.6 milhões)
TAMANHO_CENARIO_PEQUENO = 6


def verificar_otimalidade(pacientes: list) -> bool:
    """Retorna True se o custo do A* iguala o mínimo exaustivo."""
    resultado_a_estrela = executar_a_estrela(pacientes, TEMPO_CONSULTA_MINUTOS)
    custo_a_estrela = resultado_a_estrela.custo_g

    melhor_custo = math.inf
    melhor_ordem = None
    empates = 0
    total_permutacoes = 0

    for permutacao in itertools.permutations(pacientes):
        total_permutacoes += 1
        custo = calcular_risco_ordem_fixa(list(permutacao), TEMPO_CONSULTA_MINUTOS)
        if math.isclose(custo, melhor_custo):
            empates += 1
        elif custo < melhor_custo:
            melhor_custo = custo
            melhor_ordem = permutacao
            empates = 1

    print(f"Permutações avaliadas:      {total_permutacoes}")
    print(f"Menor risco (força bruta):  {melhor_custo:.2f}")
    print(f"Risco encontrado pelo A*:   {custo_a_estrela:.2f}")
    print(f"Ordem ótima (força bruta):  {' -> '.join(p.nome for p in melhor_ordem)}")
    print(f"Ordem encontrada pelo A*:   {' -> '.join(p.nome for p in resultado_a_estrela.atendidos)}")
    if empates > 1:
        print(f"(Observação: {empates} ordens distintas empatam no custo mínimo.)")

    return math.isclose(custo_a_estrela, melhor_custo)


def main() -> None:
    print("--- VERIFICAÇÃO DE OTIMALIDADE POR FORÇA BRUTA (CENÁRIO PEQUENO) ---")

    # Mesma semente e mesma ordem de sorteio dos experimentos: a fila gerada
    # aqui é idêntica à do Cenário Pequeno reportado no relatório.
    random.seed(SEMENTE_ALEATORIA)
    pacientes = carregar_pacientes_do_csv(TAMANHO_CENARIO_PEQUENO)

    if verificar_otimalidade(pacientes):
        print("RESULTADO: OK — o A* encontrou o custo mínimo global.")
    else:
        sys.exit("RESULTADO: FALHA — existe ordem com risco menor que a do A*. "
                 "Revisar a modelagem!")


if __name__ == "__main__":
    main()
