from src.models import relatorio_model
from src.models.constants import FAIXAS_DESCONTO


def calcular_desconto(faturamento):
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * taxa
    return 0


def relatorio_vendas():
    totais = relatorio_model.totais_de_vendas()
    faturamento = totais["faturamento"]
    total_pedidos = totais["total_pedidos"]
    desconto = calcular_desconto(faturamento)
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": totais["pendentes"],
        "pedidos_aprovados": totais["aprovados"],
        "pedidos_cancelados": totais["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
