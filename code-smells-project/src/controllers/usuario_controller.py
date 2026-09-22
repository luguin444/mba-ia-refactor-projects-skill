"""Handlers HTTP de usuário e login."""
from flask import jsonify, request

from src.controllers.paginacao import ler_paginacao
from src.services import usuario_service


def listar():
    limite, deslocamento = ler_paginacao()
    return jsonify({"dados": usuario_service.listar(limite, deslocamento), "sucesso": True}), 200


def buscar(id):
    return jsonify({"dados": usuario_service.buscar(id), "sucesso": True}), 200


def criar():
    usuario_id = usuario_service.criar(request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    usuario = usuario_service.autenticar(request.get_json(silent=True))
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
