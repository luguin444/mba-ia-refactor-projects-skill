"""Regra de negócio de produto. Testável sem subir servidor e sem tocar em HTTP."""
import logging

from src.middlewares.error_handler import AppError
from src.models import produto_model
from src.models.constants import (
    CATEGORIA_PADRAO,
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
)

logger = logging.getLogger(__name__)


def _validar_payload(dados: dict | None, *, validar_nome_e_categoria: bool) -> dict:
    """Valida o payload de produto e devolve os campos normalizados.

    `validar_nome_e_categoria` reproduz a assimetria que o baseline capturou: a criação
    checa tamanho do nome e lista de categorias, a atualização não. Unificar as duas
    seria mudança de contrato — ver "Divergências para decisão" no relatório.
    """
    if not dados:
        raise AppError("Dados inválidos")
    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise AppError(mensagem)

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if preco < 0:
        raise AppError("Preço não pode ser negativo")
    if estoque < 0:
        raise AppError("Estoque não pode ser negativo")

    if validar_nome_e_categoria:
        if len(nome) < NOME_PRODUTO_MIN:
            raise AppError("Nome muito curto")
        if len(nome) > NOME_PRODUTO_MAX:
            raise AppError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise AppError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def listar(limite=None, deslocamento=None) -> list[dict]:
    produtos = produto_model.listar(limite, deslocamento)
    logger.info("listando %d produtos", len(produtos))
    return produtos


def buscar(produto_id: int) -> dict:
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise AppError("Produto não encontrado", status=404, incluir_sucesso=True)
    return produto


def pesquisar(termo, categoria, preco_min, preco_max, limite=None, deslocamento=None) -> list[dict]:
    return produto_model.buscar(termo, categoria, preco_min, preco_max, limite, deslocamento)


def criar(dados: dict | None) -> int:
    campos = _validar_payload(dados, validar_nome_e_categoria=True)
    produto_id = produto_model.criar(**campos)
    logger.info("produto criado", extra={"produto_id": produto_id})
    return produto_id


def atualizar(produto_id: int, dados: dict | None) -> None:
    if not produto_model.buscar_por_id(produto_id):
        raise AppError("Produto não encontrado", status=404)
    campos = _validar_payload(dados, validar_nome_e_categoria=False)
    produto_model.atualizar(produto_id, **campos)


def deletar(produto_id: int) -> None:
    if not produto_model.buscar_por_id(produto_id):
        raise AppError("Produto não encontrado", status=404)
    produto_model.deletar(produto_id)
    logger.info("produto deletado", extra={"produto_id": produto_id})
