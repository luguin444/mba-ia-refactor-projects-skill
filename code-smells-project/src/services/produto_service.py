import logging

from src.errors import NaoEncontradoError, ValidacaoError
from src.models import produto_model
from src.models.constants import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_PRODUTO_MAX, NOME_PRODUTO_MIN

logger = logging.getLogger(__name__)


def _numerico(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar(dados):
    """Regra única de produto, usada por criação e atualização."""
    if not dados or not isinstance(dados, dict):
        raise ValidacaoError("Dados inválidos")
    for campo, mensagem in (("nome", "Nome é obrigatório"),
                            ("preco", "Preço é obrigatório"),
                            ("estoque", "Estoque é obrigatório")):
        if campo not in dados:
            raise ValidacaoError(mensagem)

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidacaoError("Nome deve ser texto")
    if not _numerico(preco):
        raise ValidacaoError("Preço deve ser numérico")
    if not _numerico(estoque):
        raise ValidacaoError("Estoque deve ser numérico")
    if preco < 0:
        raise ValidacaoError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidacaoError("Estoque não pode ser negativo")
    if len(nome) < NOME_PRODUTO_MIN:
        raise ValidacaoError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidacaoError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidacaoError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    return {"nome": nome, "descricao": descricao, "preco": preco, "estoque": estoque, "categoria": categoria}


def listar(limite=None, offset=0):
    return produto_model.listar(limite, offset)


def obter(produto_id):
    return produto_model.buscar_por_id(produto_id)


def _exigir_existente(produto_id):
    if produto_model.buscar_por_id(produto_id) is None:
        raise NaoEncontradoError("Produto não encontrado")


def buscar(termo, categoria, preco_min, preco_max):
    try:
        preco_min = float(preco_min) if preco_min else preco_min
        preco_max = float(preco_max) if preco_max else preco_max
    except ValueError:
        raise ValidacaoError("preco_min e preco_max devem ser numéricos") from None
    return produto_model.buscar(termo, categoria, preco_min, preco_max)


def criar(dados):
    campos = validar(dados)
    produto_id = produto_model.criar(**campos)
    logger.info("produto criado id=%s", produto_id)
    return produto_id


def atualizar(produto_id, dados):
    _exigir_existente(produto_id)
    produto_model.atualizar(produto_id, **validar(dados))


def remover(produto_id):
    _exigir_existente(produto_id)
    produto_model.remover(produto_id)
    logger.info("produto removido id=%s", produto_id)
