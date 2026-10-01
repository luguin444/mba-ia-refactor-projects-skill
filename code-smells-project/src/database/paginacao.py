def aplicar_limite(sql, params, limite, offset):
    """Acrescenta LIMIT/OFFSET só quando o cliente pediu; sem limite, a listagem continua inteira."""
    if limite is None:
        return sql, list(params)
    return sql + " LIMIT ? OFFSET ?", [*params, limite, offset]
