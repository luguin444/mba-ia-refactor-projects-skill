from enum import StrEnum

VERSAO_API = "1.0.0"


class StatusPedido(StrEnum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class TipoUsuario(StrEnum):
    CLIENTE = "cliente"
    ADMIN = "admin"


CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

# (faturamento mínimo exclusivo, taxa) — avaliadas da maior para a menor
FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))

LIMITE_MAXIMO_PAGINA = 200
