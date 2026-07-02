"""Módulo 2 — Algoritmo de Busca (A*).

Decide a melhor ordem de atendimento considerando a probabilidade de
gravidade alta (produzida pela rede bayesiana) e o tempo de espera:

    risco(paciente)   = P(gravidade_alta) x tempo_esperando
    custo de uma ação = risco acumulado dos pacientes que continuam esperando
"""

import heapq
from typing import Optional

# Tempo (em minutos) que cada consulta de triagem ocupa. Centralizado aqui
# para que FIFO, Gulosa e A* sejam sempre comparados sob o mesmo tempo.
TEMPO_CONSULTA_MINUTOS = 10


class Paciente:
    def __init__(self, nome: str, p_gravidade_alta: float, tempo_espera: float):
        self.nome = nome
        self.p_gravidade_alta = p_gravidade_alta
        self.tempo_espera = tempo_espera

    def risco_apos(self, tempo_adicional: float) -> float:
        """Risco projetado 'tempo_adicional' minutos à frente do tempo atual."""
        return self.p_gravidade_alta * (self.tempo_espera + tempo_adicional)

    def risco_atual(self) -> float:
        # Risco = P(alta) * tempo_esperando
        return self.risco_apos(0)


class EstadoBusca:
    """Um nó da árvore de busca do A*.

    Os objetos Paciente nunca são alterados nem clonados: o tempo extra que
    cada um acumulou na fila é derivado de 'tempo_decorrido' (minutos passados
    desde o início dos atendimentos), o que evita recriar a fila inteira a
    cada expansão de estado.
    """

    def __init__(self, fila_espera: tuple, atendidos: tuple,
                 custo_g: float, tempo_decorrido: float):
        self.fila_espera = fila_espera         # Pacientes ainda aguardando
        self.atendidos = atendidos             # Ordem de pacientes já atendidos
        self.custo_g = custo_g                 # Custo acumulado real
        self.tempo_decorrido = tempo_decorrido # Minutos desde o início

    def calcular_h(self) -> float:
        """Heurística admissível: soma dos riscos atuais menos o maior deles.

        A soma pura superestima o custo real quando resta 1 paciente (atendê-lo
        custa 0, pois ninguém continua esperando). Subtrair a maior parcela —
        que pode ser zerada de imediato na próxima consulta — garante
        h(n) <= h*(n) em todos os estados, preservando a otimalidade do A*.
        """
        riscos = [p.risco_apos(self.tempo_decorrido) for p in self.fila_espera]
        if not riscos:
            return 0.0
        return sum(riscos) - max(riscos)

    def custo_f(self) -> float:
        # F(n) = Custo G (passado) + Heurística H (futuro estimado)
        return self.custo_g + self.calcular_h()

    def __lt__(self, outro: "EstadoBusca") -> bool:
        # Necessário para o heapq ordenar a fronteira de busca pelo menor F(n)
        return self.custo_f() < outro.custo_f()


def executar_a_estrela(pacientes_iniciais: list,
                       tempo_consulta: float = TEMPO_CONSULTA_MINUTOS) -> Optional[EstadoBusca]:
    estado_inicial = EstadoBusca(fila_espera=tuple(pacientes_iniciais),
                                 atendidos=(), custo_g=0.0, tempo_decorrido=0.0)

    fronteira = [estado_inicial]

    # Closed List: melhor custo_g já visto para cada conjunto de pacientes
    # restantes. Como o tempo decorrido só depende de quantos já foram
    # atendidos, dois estados com a mesma fila restante são comparáveis por g.
    visitados: dict = {}

    while fronteira:
        estado_atual = heapq.heappop(fronteira)

        # frozenset cria um conjunto imutável que pode ser usado como chave.
        chave_estado = frozenset(p.nome for p in estado_atual.fila_espera)

        # Se já chegamos a essa combinação de pacientes restantes com custo
        # igual ou menor, ignoramos este caminho.
        if chave_estado in visitados and visitados[chave_estado] <= estado_atual.custo_g:
            continue
        visitados[chave_estado] = estado_atual.custo_g

        # Teste de objetivo: a fila está vazia?
        if not estado_atual.fila_espera:
            return estado_atual

        # Gera os sucessores: cada paciente da fila pode ser o próximo atendido
        tempo_apos_consulta = estado_atual.tempo_decorrido + tempo_consulta
        for i, paciente_alvo in enumerate(estado_atual.fila_espera):
            nova_fila = estado_atual.fila_espera[:i] + estado_atual.fila_espera[i + 1:]

            # O tempo passa e o risco de quem ficou na fila entra no custo
            custo_passo = sum(p.risco_apos(tempo_apos_consulta) for p in nova_fila)
            novo_custo_g = estado_atual.custo_g + custo_passo

            # Poda antecipada: não empilha caminhos que já sabemos ser piores
            chave_nova = frozenset(p.nome for p in nova_fila)
            if chave_nova in visitados and visitados[chave_nova] <= novo_custo_g:
                continue

            novo_estado = EstadoBusca(fila_espera=nova_fila,
                                      atendidos=estado_atual.atendidos + (paciente_alvo,),
                                      custo_g=novo_custo_g,
                                      tempo_decorrido=tempo_apos_consulta)
            heapq.heappush(fronteira, novo_estado)

    return None


def calcular_risco_ordem_fixa(ordem_pacientes: list,
                              tempo_consulta: float = TEMPO_CONSULTA_MINUTOS) -> float:
    """
    Calcula o risco acumulado de uma ordem fixa de atendimento (FIFO e Gulosa).
    Simula o avanço do tempo para os pacientes que ficam esperando, usando o
    mesmo tempo de consulta do A* para que a comparação seja justa.
    """
    custo_total = 0.0
    for posicao in range(1, len(ordem_pacientes)):
        tempo_decorrido = posicao * tempo_consulta
        custo_total += sum(p.risco_apos(tempo_decorrido)
                           for p in ordem_pacientes[posicao:])
    return custo_total


def estrategia_fifo(pacientes: list) -> list:
    """Ordena estritamente por quem está esperando há mais tempo."""
    return sorted(pacientes, key=lambda p: p.tempo_espera, reverse=True)


def estrategia_gulosa(pacientes: list) -> list:
    """Ordena estritamente por quem tem maior probabilidade de gravidade alta."""
    return sorted(pacientes, key=lambda p: p.p_gravidade_alta, reverse=True)
