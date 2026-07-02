"""Interface interativa (Streamlit) do Sistema Inteligente de Triagem.

Camada de visualização sobre os módulos existentes — nenhuma lógica de
inferência ou busca é duplicada aqui.

Executar com:
    py -3.12 -m streamlit run app_streamlit.py
"""

import random

import pandas as pd
import streamlit as st

from rede_bayesiana import obter_distribuicao_gravidade
from algoritmo_busca import (
    executar_a_estrela,
    estrategia_fifo,
    estrategia_gulosa,
    TEMPO_CONSULTA_MINUTOS,
)
from integracao_experimento import carregar_pacientes_do_csv, SEMENTE_ALEATORIA

# Rótulos legíveis para os estados de cada variável da rede
OPCOES_SINTOMAS = {
    'Febre': {0: "Normal", 1: "Alterada"},
    'Saturacao_O2': {0: "Normal (≥ 95%)", 1: "Reduzida (90–94%)", 2: "Crítica (< 90%)"},
    'Idade_Doenca': {0: "Jovem / Saudável", 1: "Idoso / Doença crônica"},
    'Pressao_Arterial': {0: "Normal", 1: "Alterada"},
    'Nivel_Dor': {0: "Leve / Moderada", 1: "Intensa"},
}

TITULOS_SINTOMAS = {
    'Febre': "Febre",
    'Saturacao_O2': "Saturação de O₂",
    'Idade_Doenca': "Idade + Doença Crônica",
    'Pressao_Arterial': "Pressão Arterial",
    'Nivel_Dor': "Nível de Dor",
}

# Acima deste tamanho de fila o A* começa a demorar visivelmente
LIMITE_PACIENTES_A_ESTRELA = 22


@st.cache_data(show_spinner=False)
def inferir_gravidade(febre: int, saturacao: int, idade: int,
                      pressao: int, dor: int) -> list:
    return obter_distribuicao_gravidade({
        'Febre': febre,
        'Saturacao_O2': saturacao,
        'Idade_Doenca': idade,
        'Pressao_Arterial': pressao,
        'Nivel_Dor': dor,
    })


def custo_acumulado_por_passo(ordem: list, tempo_consulta: float) -> list:
    """Risco acumulado após cada atendimento concluído (passo 0 = início)."""
    acumulado = [0.0]
    total = 0.0
    for posicao in range(1, len(ordem) + 1):
        tempo = posicao * tempo_consulta
        total += sum(p.risco_apos(tempo) for p in ordem[posicao:])
        acumulado.append(total)
    return acumulado


@st.cache_data(show_spinner=False)
def rodar_comparacao(n_pacientes: int, semente: int, tempo_consulta: int) -> dict:
    """Sorteia a fila e avalia FIFO, Gulosa e A* sob os mesmos parâmetros."""
    random.seed(semente)
    pacientes = carregar_pacientes_do_csv(n_pacientes)

    ordens = {
        "FIFO": estrategia_fifo(pacientes),
        "Gulosa": estrategia_gulosa(pacientes),
        "A*": list(executar_a_estrela(pacientes, tempo_consulta).atendidos),
    }

    resultado = {"fila": [(p.nome, p.p_gravidade_alta, p.tempo_espera) for p in pacientes],
                 "estrategias": {}}
    for nome, ordem in ordens.items():
        curva = custo_acumulado_por_passo(ordem, tempo_consulta)
        resultado["estrategias"][nome] = {
            "ordem": [p.nome for p in ordem],
            "curva": curva,
            "custo": curva[-1],
        }
    return resultado


st.set_page_config(page_title="Triagem Inteligente", page_icon="🏥", layout="wide")
st.title("🏥 Sistema Inteligente de Triagem em Pronto-Socorro")
st.caption("Rede Bayesiana (pgmpy) para estimar gravidade + A* para ordenar o atendimento — "
           "CK0248 · Inteligência Artificial")

aba_triagem, aba_comparacao = st.tabs([
    "🩺 Triagem individual — Rede Bayesiana",
    "📊 Comparação de estratégias — A* vs. FIFO vs. Gulosa",
])

# ---------------------------------------------------------------- Módulo 1
with aba_triagem:
    st.subheader("Estime a gravidade de um paciente")
    st.write("Informe os sinais vitais coletados na chegada. A rede bayesiana "
             "combina as evidências e produz o vetor de probabilidades de gravidade "
             "que alimenta o A*.")

    colunas = st.columns(len(OPCOES_SINTOMAS))
    evidencias = {}
    for coluna, (variavel, opcoes) in zip(colunas, OPCOES_SINTOMAS.items()):
        with coluna:
            evidencias[variavel] = st.selectbox(
                TITULOS_SINTOMAS[variavel],
                options=list(opcoes.keys()),
                format_func=lambda estado, opcoes=opcoes: opcoes[estado],
                key=f"sintoma_{variavel}",
            )

    p_baixa, p_media, p_alta = inferir_gravidade(
        evidencias['Febre'], evidencias['Saturacao_O2'], evidencias['Idade_Doenca'],
        evidencias['Pressao_Arterial'], evidencias['Nivel_Dor'],
    )

    st.divider()
    col_baixa, col_media, col_alta = st.columns(3)
    col_baixa.metric("P(Gravidade = baixa)", f"{p_baixa:.0%}")
    col_media.metric("P(Gravidade = média)", f"{p_media:.0%}")
    col_alta.metric("P(Gravidade = alta)", f"{p_alta:.0%}")

    nivel_mais_provavel = max(
        [("baixa", p_baixa), ("média", p_media), ("alta", p_alta)],
        key=lambda item: item[1],
    )[0]
    if nivel_mais_provavel == "alta":
        st.error(f"Classificação mais provável: gravidade **ALTA** — "
                 f"este paciente entra no A* com peso {p_alta:.2f} por minuto de espera.")
    elif nivel_mais_provavel == "média":
        st.warning("Classificação mais provável: gravidade **MÉDIA**.")
    else:
        st.success("Classificação mais provável: gravidade **BAIXA**.")

    grafico = pd.DataFrame(
        {"Probabilidade": [p_baixa, p_media, p_alta]},
        index=["Baixa", "Média", "Alta"],
    )
    st.bar_chart(grafico, horizontal=True, height=220)

# ---------------------------------------------------------------- Módulo 2
with aba_comparacao:
    st.subheader("Como cada estratégia esvazia a mesma fila?")

    col_n, col_semente, col_tempo = st.columns(3)
    n_pacientes = col_n.slider("Pacientes na fila", min_value=5,
                               max_value=LIMITE_PACIENTES_A_ESTRELA, value=6)
    semente = col_semente.number_input("Semente aleatória", min_value=0,
                                       value=SEMENTE_ALEATORIA,
                                       help="Mesma semente = mesma fila sorteada "
                                            "(42 reproduz os números do relatório).")
    tempo_consulta = col_tempo.slider("Tempo de consulta (min)", min_value=5,
                                      max_value=30, value=TEMPO_CONSULTA_MINUTOS)

    if n_pacientes > 20:
        st.info("Filas acima de 20 pacientes podem levar mais tempo — "
                "o espaço de busca do A* cresce exponencialmente.")

    try:
        with st.spinner("Executando FIFO, Gulosa e A*..."):
            dados = rodar_comparacao(n_pacientes, int(semente), tempo_consulta)
    except SystemExit as erro:
        st.error(str(erro))
        st.stop()

    estrategias = dados["estrategias"]
    custo_fifo = estrategias["FIFO"]["custo"]

    st.divider()
    colunas_metricas = st.columns(3)
    for coluna, nome in zip(colunas_metricas, ["FIFO", "Gulosa", "A*"]):
        custo = estrategias[nome]["custo"]
        delta = None if nome == "FIFO" else f"-{(1 - custo / custo_fifo) * 100:.1f}% vs. FIFO"
        coluna.metric(f"Risco acumulado — {nome}", f"{custo:.2f}",
                      delta=delta, delta_color="inverse")

    melhor = min(estrategias, key=lambda nome: estrategias[nome]["custo"])
    if melhor == "A*":
        st.success("✅ O A* encontrou a ordem de menor risco acumulado, como esperado.")
    else:
        st.error(f"⚠️ {melhor} superou o A* — algo na modelagem precisa ser revisado!")

    col_curva, col_fila = st.columns([3, 2])

    with col_curva:
        st.markdown("**Risco acumulado a cada atendimento concluído**")
        curvas = pd.DataFrame({nome: info["curva"] for nome, info in estrategias.items()})
        curvas.index.name = "Atendimentos concluídos"
        st.line_chart(curvas, height=320)

    with col_fila:
        st.markdown("**Fila sorteada (entrada dos algoritmos)**")
        fila = pd.DataFrame(dados["fila"],
                            columns=["Paciente", "P(gravidade alta)", "Espera inicial (min)"])
        st.dataframe(fila, height=320, hide_index=True)

    st.markdown("**Ordem de atendimento decidida por cada estratégia**")
    ordens = pd.DataFrame({nome: info["ordem"] for nome, info in estrategias.items()})
    ordens.index = ordens.index + 1
    ordens.index.name = "Posição"
    st.dataframe(ordens)
