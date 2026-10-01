from src.database.connection import get_db


def contagens():
    conexao = get_db()
    conexao.execute("SELECT 1")
    return {
        "produtos": conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
        "usuarios": conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
        "pedidos": conexao.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
    }
