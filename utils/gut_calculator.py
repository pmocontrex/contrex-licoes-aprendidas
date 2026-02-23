def calcular_gut(gravidade: int, urgencia: int, tendencia: int) -> dict:
    resultado = gravidade * urgencia * tendencia
    if resultado <= 25:
        nivel, cor, label = "baixo", "🟢", "Baixo"
    elif resultado <= 74:
        nivel, cor, label = "medio", "🟡", "Médio"
    else:
        nivel, cor, label = "alto",  "🔴", "Alto"
    return {"resultado": resultado, "nivel": nivel, "cor": cor, "label": label}


_DESC_GRAVIDADE = {
    1: "Sem gravidade — nenhum impacto relevante",
    2: "Pouco grave — impacto pequeno e facilmente reversível",
    3: "Moderadamente grave — impacto considerável mas gerenciável",
    4: "Grave — grande impacto com dificuldade de reversão",
    5: "Extremamente grave — impacto catastrófico ou irreversível",
}
_DESC_URGENCIA = {
    1: "Pode esperar — não há pressão de tempo",
    2: "Pouco urgente — pode ser tratado nas próximas semanas",
    3: "Urgente — requer atenção em breve",
    4: "Muito urgente — requer ação imediata nos próximos dias",
    5: "Urgentíssimo e inadiável — ação imediata necessária",
}
_DESC_TENDENCIA = {
    1: "Manterá estabilidade — situação não tende a piorar",
    2: "Irá piorar a longo prazo",
    3: "Irá piorar a médio prazo",
    4: "Irá piorar a curto prazo",
    5: "Piora imediata — situação se agravará rapidamente",
}


def get_descricao_gravidade(nivel: int) -> str:
    return _DESC_GRAVIDADE.get(nivel, "")

def get_descricao_urgencia(nivel: int) -> str:
    return _DESC_URGENCIA.get(nivel, "")

def get_descricao_tendencia(nivel: int) -> str:
    return _DESC_TENDENCIA.get(nivel, "")
