"""Regra de negócio de usuário e autenticação."""
import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.middlewares.error_handler import AppError
from src.models import usuario_model
from src.models.serializers import serializar_usuario_autenticado

logger = logging.getLogger(__name__)


def listar(limite=None, deslocamento=None) -> list[dict]:
    return usuario_model.listar(limite, deslocamento)


def buscar(usuario_id: int) -> dict:
    usuario = usuario_model.buscar_por_id(usuario_id)
    if not usuario:
        raise AppError("Usuário não encontrado", status=404)
    return usuario


def criar(dados: dict | None) -> int:
    if not dados:
        raise AppError("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise AppError("Nome, email e senha são obrigatórios")

    # A senha nunca chega ao banco em texto claro.
    usuario_id = usuario_model.criar(nome, email, generate_password_hash(senha))
    logger.info("usuário criado", extra={"usuario_id": usuario_id})
    return usuario_id


def autenticar(dados: dict | None) -> dict:
    """Verifica a senha na aplicação — antes a comparação acontecia dentro do WHERE."""
    dados = dados or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        raise AppError("Email e senha são obrigatórios")

    linha = usuario_model.buscar_linha_por_email(email)
    if linha is None or not check_password_hash(linha["senha"], senha):
        logger.info("tentativa de login recusada")
        raise AppError("Email ou senha inválidos", status=401, incluir_sucesso=True)

    logger.info("login bem-sucedido", extra={"usuario_id": linha["id"]})
    return serializar_usuario_autenticado(linha)
