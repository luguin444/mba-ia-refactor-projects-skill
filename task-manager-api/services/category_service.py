from exceptions import NotFoundError, ValidationError
from models.category import Category
from models.constants import DEFAULT_CATEGORY_COLOR
from repositories import category_repository, task_repository, unit_of_work


def get_or_404(category_id):
    category = category_repository.get(category_id)
    if category is None:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_with_task_count(page=None):
    task_counts = task_repository.count_by_category()
    return [
        {**category.to_dict(), 'task_count': task_counts.get(category.id, 0)}
        for category in category_repository.list_all(page)
    ]


def create(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')

    category = Category(
        name=name,
        description=data.get('description', ''),
        color=data.get('color', DEFAULT_CATEGORY_COLOR),
    )
    unit_of_work.add(category)
    unit_of_work.commit('Erro ao criar categoria')
    return category.to_dict()


def update(category, data):
    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    unit_of_work.commit('Erro ao atualizar')
    return category.to_dict()


def delete(category_id):
    category = get_or_404(category_id)
    unit_of_work.delete(category)  # tasks da categoria ficam com category_id nulo
    unit_of_work.commit('Erro ao deletar')
