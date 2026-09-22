"""Constantes de domínio. Fonte única para valores que antes eram literais soltos."""
from enum import StrEnum


class StatusPedido(StrEnum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class CategoriaProduto(StrEnum):
    INFORMATICA = "informatica"
    MOVEIS = "moveis"
    VESTUARIO = "vestuario"
    GERAL = "geral"
    ELETRONICOS = "eletronicos"
    LIVROS = "livros"


# A ordem é contrato: a mensagem de erro de categoria inválida lista os valores.
CATEGORIAS_VALIDAS = [c.value for c in CategoriaProduto]
STATUS_VALIDOS = [s.value for s in StatusPedido]

CATEGORIA_PADRAO = CategoriaProduto.GERAL.value

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# Faixas de desconto sobre o faturamento, da mais alta para a mais baixa.
FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))

LIMITE_PAGINACAO_MAXIMO = 200
