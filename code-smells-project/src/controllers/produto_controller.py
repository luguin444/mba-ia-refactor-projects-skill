"""Handlers HTTP de produto. Sem SQL, sem regra — traduz request em chamada de serviço."""
from flask import jsonify, request

from src.controllers.paginacao import ler_paginacao
from src.services import produto_service


def listar():
    limite, deslocamento = ler_paginacao()
    return jsonify({"dados": produto_service.listar(limite, deslocamento), "sucesso": True}), 200


def buscar(id):
    return jsonify({"dados": produto_service.buscar(id), "sucesso": True}), 200


def pesquisar():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    limite, deslocamento = ler_paginacao()
    resultados = produto_service.pesquisar(termo, categoria, preco_min, preco_max, limite, deslocamento)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar():
    produto_id = produto_service.criar(request.get_json(silent=True))
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(id):
    produto_service.atualizar(id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(id):
    produto_service.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
