from flask import jsonify, request

from src.controllers.paginacao import ler_paginacao
from src.middlewares.auth import exigir_dono_ou_admin
from src.services import pedido_service


def criar():
    usuario_id, itens = pedido_service.validar(request.get_json(silent=True))
    exigir_dono_ou_admin(usuario_id)
    resultado = pedido_service.criar(usuario_id, itens)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar():
    return jsonify({"dados": pedido_service.listar(*ler_paginacao()), "sucesso": True}), 200


def listar_por_usuario(usuario_id):
    pedidos = pedido_service.listar_por_usuario(usuario_id, *ler_paginacao())
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status(pedido_id):
    pedido_service.atualizar_status(pedido_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
