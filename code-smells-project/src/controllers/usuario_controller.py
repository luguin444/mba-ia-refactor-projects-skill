from flask import jsonify, request

from src.controllers.paginacao import ler_paginacao
from src.services import usuario_service


def listar():
    return jsonify({"dados": usuario_service.listar(*ler_paginacao()), "sucesso": True}), 200


def buscar(usuario_id):
    return jsonify({"dados": usuario_service.obter(usuario_id), "sucesso": True}), 200


def criar():
    usuario_id = usuario_service.cadastrar(request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    usuario, token = usuario_service.autenticar(request.get_json(silent=True))
    return jsonify({"dados": usuario, "token": token, "sucesso": True, "mensagem": "Login OK"}), 200
