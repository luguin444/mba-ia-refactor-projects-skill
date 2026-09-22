"""Handlers HTTP de pedido."""
from flask import jsonify, request

from src.services import pedido_service


def listar():
    return jsonify({"dados": pedido_service.listar(), "sucesso": True}), 200


def listar_por_usuario(usuario_id):
    return jsonify({"dados": pedido_service.listar_por_usuario(usuario_id), "sucesso": True}), 200


def criar():
    resultado = pedido_service.criar(request.get_json(silent=True))
    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso",
    }), 201


def atualizar_status(pedido_id):
    pedido_service.atualizar_status(pedido_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
