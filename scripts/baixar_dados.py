"""
Baixa a taxa de desocupação trimestral da PNAD Contínua (IBGE, tabela 4099)
para Brasil, grandes regiões e UFs, e salva em data/desocupacao_trimestral.csv.

Uso:
    python scripts/baixar_dados.py

Fonte: https://sidra.ibge.gov.br/tabela/4099
O mesmo extrator, com retry e testes, está no projeto
https://github.com/jonathansilvadesa-sys/etl-pipeline-dados-abertos
"""

from datetime import date
from pathlib import Path

import pandas as pd
import requests

URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/4099/periodos/"
    "{inicio}-{fim}/variaveis/4099"
)
NIVEIS = {"N1": "Brasil", "N2": "Região", "N3": "UF"}
SIGLAS = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}
REGIAO_DA_UF = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
DESTINO = Path(__file__).resolve().parent.parent / "data" / "desocupacao_trimestral.csv"


def baixar() -> pd.DataFrame:
    url = URL.format(inicio="201201", fim=f"{date.today().year}04")
    resposta = requests.get(url, params={"localidades": "N1[all]|N2[all]|N3[all]"}, timeout=60)
    resposta.raise_for_status()

    linhas = []
    for serie in resposta.json()[0]["resultados"][0]["series"]:
        local = serie["localidade"]
        nivel = NIVEIS[local["nivel"]["id"]]
        for periodo, valor in serie["serie"].items():
            if valor in ("..", "...", "X", ""):
                continue
            linhas.append({
                "nivel": nivel,
                "codigo": local["id"],
                "local": local["nome"],
                "sigla": SIGLAS.get(local["id"]) if nivel == "UF" else None,
                "regiao": (REGIAO_DA_UF[local["id"][0]] if nivel == "UF"
                           else local["nome"] if nivel == "Região" else None),
                "ano": int(periodo[:4]),
                "trimestre": int(periodo[4:]),
                "taxa_desocupacao": float(valor),
            })
    return pd.DataFrame(linhas).sort_values(["nivel", "codigo", "ano", "trimestre"])


if __name__ == "__main__":
    df = baixar()
    DESTINO.parent.mkdir(exist_ok=True)
    df.to_csv(DESTINO, index=False)
    ultimo = df[["ano", "trimestre"]].drop_duplicates().iloc[-1]
    print(f"{len(df)} linhas salvas em {DESTINO.name} "
          f"(1º tri/2012 a {ultimo.trimestre}º tri/{ultimo.ano})")
