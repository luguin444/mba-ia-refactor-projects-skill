from flask import jsonify, request

from src.controllers.paginacao import ler_paginacao
from src.errors import NaoEncontradoError
from src.services import produto_service


def listar():
    produtos = produto_service.listar(*ler_paginacao())
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar(produto_id):
    produto = produto_service.obter(produto_id)
    if produto is None:
        raise NaoEncontradoError("Produto não encontrado", com_sucesso=True)
    return jsonify({"dados": produto, "sucesso": True}), 200


def pesquisar():
    resultados = produto_service.buscar(
        request.args.get("q", ""),
        request.args.get("categoria"),
        request.args.get("preco_min"),
        request.args.get("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar():
    produto_id = produto_service.criar(request.get_json(silent=True))
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(produto_id):
    produto_service.atualizar(produto_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def remover(produto_id):
    produto_service.remover(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
