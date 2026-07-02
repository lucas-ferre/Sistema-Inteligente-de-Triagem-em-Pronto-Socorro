"""Orquestração dos experimentos: compara FIFO, Gulosa e A*.

Todas as estratégias são avaliadas com o MESMO tempo de consulta
(TEMPO_CONSULTA_MINUTOS) e com semente aleatória fixa, garantindo uma
comparação justa e resultados reprodutíveis.
"""

import random
import csv
import sys
from algoritmo_busca import (
    Paciente,
    executar_a_estrela,
    estrategia_fifo,
    estrategia_gulosa,
    calcular_risco_ordem_fixa,
    TEMPO_CONSULTA_MINUTOS,
)

SEMENTE_ALEATORIA = 42

# Faixa (em minutos) do tempo de espera inicial sorteado para cada paciente
TEMPO_ESPERA_MINIMO = 5
TEMPO_ESPERA_MAXIMO = 60


def carregar_pacientes_do_csv(quantidade: int,
                              nome_arquivo: str = "base_pacientes_simulados.csv") -> list:
    todos_pacientes = []

    try:
        with open(nome_arquivo, mode='r', encoding='utf-8') as arquivo:
            leitor = csv.DictReader(arquivo, delimiter=';')

            for linha in leitor:
                nome = linha["ID_Paciente"]
                p_alta = float(linha["Probabilidade_Gravidade_Alta"])
                todos_pacientes.append((nome, p_alta))
    except FileNotFoundError:
        sys.exit(f"ERRO: arquivo '{nome_arquivo}' não encontrado. "
                 "Execute primeiro: python gerar_base_dados.py")
    except (KeyError, TypeError, ValueError):
        sys.exit(f"ERRO: o arquivo '{nome_arquivo}' não tem o formato esperado "
                 "(delimitador ';' e colunas ID_Paciente / Probabilidade_Gravidade_Alta). "
                 "Gere a base novamente com: python gerar_base_dados.py")

    if quantidade > len(todos_pacientes):
        sys.exit(f"ERRO: o cenário pede {quantidade} pacientes, mas a base "
                 f"'{nome_arquivo}' contém apenas {len(todos_pacientes)}.")

    pacientes_sorteados = random.sample(todos_pacientes, quantidade)

    fila_objetos = []
    for nome, p_alta in pacientes_sorteados:
        tempo_espera = random.randint(TEMPO_ESPERA_MINIMO, TEMPO_ESPERA_MAXIMO)
        fila_objetos.append(Paciente(nome, p_alta, tempo_espera))

    return fila_objetos


def executar_comparativo(pacientes_iniciais: list, nome_cenario: str) -> None:
    print(f"\n=== {nome_cenario.upper()} ({len(pacientes_iniciais)} PACIENTES, "
          f"consulta de {TEMPO_CONSULTA_MINUTOS} min) ===")

    # FIFO: atende na ordem de chegada (quem espera há mais tempo primeiro)
    ordem_fifo = estrategia_fifo(pacientes_iniciais)
    custo_fifo = calcular_risco_ordem_fixa(ordem_fifo, TEMPO_CONSULTA_MINUTOS)

    # Gulosa: atende sempre o de maior P(gravidade alta)
    ordem_gulosa = estrategia_gulosa(pacientes_iniciais)
    custo_gulosa = calcular_risco_ordem_fixa(ordem_gulosa, TEMPO_CONSULTA_MINUTOS)

    # A*: minimiza o risco acumulado considerando gravidade E tempo de espera
    resultado_a_estrela = executar_a_estrela(pacientes_iniciais, TEMPO_CONSULTA_MINUTOS)
    custo_a_estrela = resultado_a_estrela.custo_g

    print(f"{'Estratégia':<12} | {'Risco acumulado':>15} | {'vs. FIFO':>9}")
    print(f"{'-' * 12} | {'-' * 15} | {'-' * 9}")
    for nome, custo in [("FIFO", custo_fifo),
                        ("Gulosa", custo_gulosa),
                        ("A*", custo_a_estrela)]:
        reducao = (1 - custo / custo_fifo) * 100 if custo_fifo else 0.0
        coluna_reducao = "-" if nome == "FIFO" else f"-{reducao:.1f}%"
        print(f"{nome:<12} | {custo:>15.2f} | {coluna_reducao:>9}")

    if custo_a_estrela > min(custo_fifo, custo_gulosa):
        print("ATENÇÃO: o A* NÃO produziu o menor risco — revisar a modelagem!")

    if len(pacientes_iniciais) <= 8:
        ordem = " -> ".join(p.nome for p in resultado_a_estrela.atendidos)
        print(f"Ordem ótima do A*: {ordem}")


def rodar_experimentos_finais() -> None:
    print("--- INICIANDO BATERIA DE TESTES GERAIS ---")
    random.seed(SEMENTE_ALEATORIA)

    pacientes_pequeno = carregar_pacientes_do_csv(6)
    executar_comparativo(pacientes_pequeno, "Cenário Pequeno")

    print("\n(Calculando rotas do Cenário Médio. Isso pode levar alguns segundos...)")
    pacientes_medio = carregar_pacientes_do_csv(20)
    executar_comparativo(pacientes_medio, "Cenário Médio")


if __name__ == "__main__":
    rodar_experimentos_finais()
