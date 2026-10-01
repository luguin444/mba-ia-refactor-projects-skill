"""Fonte única do formato público de cada entidade."""


def produto(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def usuario(row):
    # `senha` nunca sai daqui (AP-04)
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def usuario_autenticado(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
    }


def pedido(row):
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": [],
    }


def item_pedido(row):
    return {
        "produto_id": row["produto_id"],
        "produto_nome": row["produto_nome"] if row["produto_existe"] is not None else "Desconhecido",
        "quantidade": row["quantidade"],
        "preco_unitario": row["preco_unitario"],
    }
