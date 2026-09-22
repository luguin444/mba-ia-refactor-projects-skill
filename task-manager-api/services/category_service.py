"""Regra de negócio de Category."""
import logging

from exceptions import AppError, NotFoundError
from models.category import Category
from models.constants import DEFAULT_COLOR
from repositories import category_repository, task_repository, unit_of_work

logger = logging.getLogger(__name__)


def get_category(category_id: int) -> Category:
    category = category_repository.get_by_id(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_with_task_count(*, limit=None, offset=None) -> list[tuple[Category, int]]:
    """Categorias com a contagem de tasks, em duas consultas no lugar de 1+N."""
    categories = category_repository.list_all(limit=limit, offset=offset)
    contagens = task_repository.count_by_category()
    return [(category, contagens.get(category.id, 0)) for category in categories]


def create_category(data: dict) -> Category:
    if not data:
        raise AppError('Dados inválidos')

    name = data.get('name')
    if not name:
        raise AppError('Nome é obrigatório')

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', DEFAULT_COLOR)

    category_repository.add(category)
    unit_of_work.commit()
    logger.info('categoria criada', extra={'category_id': category.id})
    return category


def update_category(category_id: int, data: dict) -> Category:
    category = get_category(category_id)
    # Sem guard de corpo vazio: `PUT` com `{}` é "não altere nada" e responde
    # 200, como no contrato atual. O `POST` exige `name` porque cria o registro.
    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    unit_of_work.commit()
    logger.info('categoria atualizada', extra={'category_id': category.id})
    return category


def delete_category(category_id: int) -> None:
    """Remove a categoria. As tasks vinculadas perdem o vínculo, não são apagadas."""
    category = get_category(category_id)
    category_repository.remove(category)
    unit_of_work.commit()
    logger.info('categoria removida', extra={'category_id': category_id})
