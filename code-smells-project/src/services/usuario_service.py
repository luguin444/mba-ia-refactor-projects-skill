import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.errors import NaoAutenticadoError, NaoEncontradoError, ValidacaoError
from src.models import serializers, usuario_model
from src.models.constants import TipoUsuario
from src.services import token_service

logger = logging.getLogger(__name__)


def listar(limite=None, offset=0):
    return usuario_model.listar(limite, offset)


def obter(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario is None:
        raise NaoEncontradoError("Usuário não encontrado")
    return usuario


def cadastrar(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidacaoError("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidacaoError("Nome, email e senha são obrigatórios")

    # O papel nunca vem do corpo: cadastro público cria sempre cliente.
    usuario_id = usuario_model.criar(nome, email, generate_password_hash(senha), TipoUsuario.CLIENTE)
    logger.info("usuário criado id=%s", usuario_id)
    return usuario_id


def autenticar(dados):
    """Devolve (usuario_publico, token). Credencial inválida levanta 401."""
    dados = dados if isinstance(dados, dict) else {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidacaoError("Email e senha são obrigatórios")

    row = usuario_model.buscar_credenciais_por_email(email)
    if row is None or not check_password_hash(row["senha"], str(senha)):
        logger.info("login recusado")
        raise NaoAutenticadoError("Email ou senha inválidos", com_sucesso=True)

    usuario = serializers.usuario_autenticado(row)
    logger.info("login ok id=%s", usuario["id"])
    return usuario, token_service.emitir(usuario)
