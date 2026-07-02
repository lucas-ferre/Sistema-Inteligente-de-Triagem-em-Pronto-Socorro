"""Gera a base simulada de pacientes usada nos experimentos.

Os sintomas são sorteados com distribuições ponderadas — alinhadas às CPTs
a priori da rede bayesiana — para refletir a triagem de um pronto-socorro
real (ex.: apenas ~10% dos pacientes chegam com saturação de O2 crítica,
e não 33% como uma escolha uniforme produziria).
"""

import random
import csv
from rede_bayesiana import obter_probabilidade_gravidade

SEMENTE_ALEATORIA = 42

# (valores possíveis, probabilidades) de cada sintoma, espelhando as CPTs
# a priori definidas em rede_bayesiana.py
DISTRIBUICAO_SINTOMAS = {
    'Febre':            ([0, 1],    [0.60, 0.40]),
    'Saturacao_O2':     ([0, 1, 2], [0.70, 0.20, 0.10]),
    'Idade_Doenca':     ([0, 1],    [0.50, 0.50]),
    'Pressao_Arterial': ([0, 1],    [0.70, 0.30]),
    'Nivel_Dor':        ([0, 1],    [0.60, 0.40]),
}


def sortear_sintomas() -> dict:
    return {
        sintoma: random.choices(valores, weights=pesos)[0]
        for sintoma, (valores, pesos) in DISTRIBUICAO_SINTOMAS.items()
    }


def gerar_base_csv(quantidade: int = 100,
                   nome_arquivo: str = "base_pacientes_simulados.csv") -> None:
    print(f"Gerando base de dados com {quantidade} pacientes...")
    random.seed(SEMENTE_ALEATORIA)

    # Cabeçalho do arquivo CSV
    cabecalho = [
        "ID_Paciente", "Febre", "Saturacao_O2", "Idade_Doenca",
        "Pressao_Arterial", "Nivel_Dor", "Probabilidade_Gravidade_Alta"
    ]

    dados_pacientes = []

    for i in range(1, quantidade + 1):
        sintomas = sortear_sintomas()

        p_alta = obter_probabilidade_gravidade(sintomas)

        linha = [
            f"Paciente_{i:03d}",
            sintomas['Febre'],
            sintomas['Saturacao_O2'],
            sintomas['Idade_Doenca'],
            sintomas['Pressao_Arterial'],
            sintomas['Nivel_Dor'],
            round(p_alta, 4)  # Arredonda para 4 casas decimais
        ]
        dados_pacientes.append(linha)

    try:
        with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as arquivo:
            escritor = csv.writer(arquivo, delimiter=';')
            escritor.writerow(cabecalho)
            escritor.writerows(dados_pacientes)
    except OSError as erro:
        print(f"ERRO: não foi possível salvar '{nome_arquivo}': {erro}")
        print("Verifique se o arquivo não está aberto em outro programa (ex.: Excel).")
        return

    print(f"Sucesso! Arquivo '{nome_arquivo}' salvo na sua pasta.")


if __name__ == "__main__":
    gerar_base_csv(100)
