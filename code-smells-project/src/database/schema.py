from src.database.connection import transacao

# itens_pedido.produto_id não tem FOREIGN KEY de propósito: o que fazer ao apagar
# um produto com histórico de venda é decisão de produto (ver relatório, AP-24).
DDL = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT NOT NULL DEFAULT '',
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL,
        categoria TEXT NOT NULL DEFAULT 'geral',
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
        status TEXT NOT NULL DEFAULT 'pendente',
        total REAL NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL
    )
    """,
)


def criar_schema():
    with transacao() as conexao:
        for comando in DDL:
            conexao.execute(comando)
