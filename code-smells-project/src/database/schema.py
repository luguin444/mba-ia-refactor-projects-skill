"""DDL das tabelas. Executado por comando explícito, nunca ao obter uma conexão."""
import sqlite3

# `usuarios.email` não recebeu UNIQUE e `itens_pedido.produto_id` não recebeu FOREIGN KEY:
# o baseline capturou cadastro com email duplicado respondendo 201 e exclusão de produto
# referenciado por um pedido respondendo 200. Aplicar as duas constraints mudaria o
# contrato — ver "Divergências para decisão" no relatório da Fase 3.
DDL = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        nome       TEXT    NOT NULL,
        descricao  TEXT    NOT NULL DEFAULT '',
        preco      REAL    NOT NULL,
        estoque    INTEGER NOT NULL,
        categoria  TEXT    NOT NULL DEFAULT 'geral',
        ativo      INTEGER NOT NULL DEFAULT 1,
        criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        nome       TEXT NOT NULL,
        email      TEXT NOT NULL,
        senha      TEXT NOT NULL,
        tipo       TEXT NOT NULL DEFAULT 'cliente',
        criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
        status     TEXT    NOT NULL DEFAULT 'pendente',
        total      REAL    NOT NULL DEFAULT 0,
        criado_em  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id      INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
        produto_id     INTEGER NOT NULL,
        quantidade     INTEGER NOT NULL,
        preco_unitario REAL    NOT NULL
    )
    """,
)


def criar_schema(conexao: sqlite3.Connection) -> None:
    for comando in DDL:
        conexao.execute(comando)
    conexao.commit()
