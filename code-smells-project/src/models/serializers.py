"""Fonte única do formato de cada recurso na resposta.

Antes o dicionário de produto era remontado em três funções e o de usuário em duas —
foi assim que o campo `senha` acabou exposto em dois deles.
"""
import sqlite3


def serializar_produto(linha: sqlite3.Row) -> dict:
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "descricao": linha["descricao"],
        "preco": linha["preco"],
        "estoque": linha["estoque"],
        "categoria": linha["categoria"],
        "ativo": linha["ativo"],
        "criado_em": linha["criado_em"],
    }


def serializar_usuario(linha: sqlite3.Row) -> dict:
    """Nunca inclui `senha`. É o único lugar que decide o que um usuário expõe."""
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "email": linha["email"],
        "tipo": linha["tipo"],
        "criado_em": linha["criado_em"],
    }


def serializar_usuario_autenticado(linha: sqlite3.Row) -> dict:
    """Forma reduzida devolvida pelo login."""
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "email": linha["email"],
        "tipo": linha["tipo"],
    }


def serializar_item_pedido(linha: sqlite3.Row) -> dict:
    return {
        "produto_id": linha["produto_id"],
        "produto_nome": linha["produto_nome"] or "Desconhecido",
        "quantidade": linha["quantidade"],
        "preco_unitario": linha["preco_unitario"],
    }


def serializar_pedido(linha: sqlite3.Row) -> dict:
    return {
        "id": linha["id"],
        "usuario_id": linha["usuario_id"],
        "status": linha["status"],
        "total": linha["total"],
        "criado_em": linha["criado_em"],
        "itens": [],
    }
