"""Política comercial de desconto e montagem do relatório de vendas.

As faixas eram números soltos dentro de uma função de acesso a dados; agora são
constante nomeada e a regra é exercitável sem banco.
"""
from src.models import relatorio_model
from src.models.constants import FAIXAS_DESCONTO


def calcular_desconto(faturamento: float) -> float:
    """Aplica a faixa mais alta que o faturamento alcança.

    Devolve `0` (int) e não `0.0` quando nenhuma faixa se aplica, porque o corpo da
    resposta capturado no baseline traz `0` para base sem faturamento.
    """
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * taxa
    return 0


def vendas() -> dict:
    agregado = relatorio_model.agregar_vendas()
    faturamento = agregado["faturamento"]
    total_pedidos = agregado["total_pedidos"]
    desconto = calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": agregado["pendentes"],
        "pedidos_aprovados": agregado["aprovados"],
        "pedidos_cancelados": agregado["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
