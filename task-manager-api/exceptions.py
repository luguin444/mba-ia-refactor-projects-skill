class AppError(Exception):
    """Erro de domínio com mensagem e status HTTP; traduzido em JSON pelo middleware de erro."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


class ValidationError(AppError):
    def __init__(self, message):
        super().__init__(message, 400)


class NotFoundError(AppError):
    def __init__(self, message):
        super().__init__(message, 404)


class ConflictError(AppError):
    def __init__(self, message):
        super().__init__(message, 409)


class UnauthorizedError(AppError):
    def __init__(self, message):
        super().__init__(message, 401)


class ForbiddenError(AppError):
    def __init__(self, message):
        super().__init__(message, 403)
