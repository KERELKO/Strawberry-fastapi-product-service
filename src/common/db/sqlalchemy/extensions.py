from typing import Any, Callable, Type, TypeVar

import sqlalchemy as sql

from src.common.exceptions import ObjectDoesNotExistException
from src.common.base.dto import BaseDTO, Entity
from src.common.utils import raise_exc
from src.common.utils.fields import SelectedFields
from src.users.dto import UserDTO
from src.products.dto import ReviewDTO, ProductDTO

from .models import User, Product, Review


MODELS_RELATED_TO_DTO = {
    User: UserDTO,
    Product: ProductDTO,
    Review: ReviewDTO,
}

SQLAlchemyModel = TypeVar('SQLAlchemyModel', bound=User | Product | Review)
TypeDTO = TypeVar('TypeDTO', bound=BaseDTO)


class MetaSQLAlchemyRepository(type):
    """
    Extends subclass repository with the following methods:
    * create
    * update
    * delete
    * _construct_select_query
    * _execute_query

    All async.
    The subclass must implement Meta class inside with variable that contains SQLAlchemy model type
    """
    def __new__(
        meta_cls,  # type: ignore
        cls_name: str,
        bases: tuple[Type[Any], ...],
        cls_dict: dict[str, Any]
    ) -> 'MetaSQLAlchemyRepository':
        if 'Meta' in cls_dict:
            model = cls_dict['Meta'].model
            cls_dict['create'] = _create_method(model)
            cls_dict['update'] = _update_method(model)
            cls_dict['delete'] = _delete_method(model)
            cls_dict['_construct_select_query'] = _select_query_constructor(model=model)
            cls_dict['_execute_query'] = _query_executor()
        return super().__new__(meta_cls, cls_name, bases, cls_dict)


def sqlalchemy_repo_extended(
    cls: type | None = None,
    get: bool = True,
    create: bool = True,
    update: bool = True,
    delete: bool = True,
    query_executor: bool = True,
) -> Callable | type:
    """
    Can extend repository class with the following methods:
    * get
    * create
    * update
    * delete

    if query_executor is True:
    * _construct_select_query
    * _execute_query

    All async.
    The class must implement Meta class inside with variable that contains SQLAlchemy model type
    """

    def wrapper(cls) -> type:
        if 'Meta' not in cls.__dict__:
            raise AttributeError(
                f'{cls.__name__} does not have "Meta" class inside, with defined sqlalchemy model'
            )
        model = cls.__dict__['Meta'].model
        if create:
            setattr(cls, 'create', _create_method(model=model))
        if delete:
            setattr(cls, 'delete', _delete_method(model=model))
        if update:
            setattr(cls, 'update', _update_method(model=model))
        if get:
            setattr(cls, 'get', _get_method(model=model))
        if query_executor:
            setattr(cls, '_construct_select_query', _select_query_constructor(model=model))
            setattr(cls, '_execute_query', _query_executor())
        return cls

    # with params: @sqlalchemy_repo_extended(...)
    if cls is None:
        return wrapper

    # without params: @sqlalchemy_repo_extended
    return wrapper(cls)


def _create_method(model: Type[SQLAlchemyModel]) -> Callable:
    async def create(self, dto: TypeDTO, commit_after_creation: bool = True) -> TypeDTO:
        values = dto.model_dump()
        new_entity = model(**values)
        self.session.add(new_entity)
        if commit_after_creation:
            await self.session.commit()
            dto.id = new_entity.id
        return dto
    return create


def _get_method(model: Type[SQLAlchemyModel]) -> Callable:
    async def get(self, id: int, fields: list[SelectedFields]) -> TypeDTO:
        values = await self._execute_query(fields=fields, id=id, first=True)
        if not values:
            raise ObjectDoesNotExistException(model.__name__, object_id=id)
        data = {}
        for i, field in enumerate(fields[0].fields):
            data[field] = values[i]
        dto_class = MODELS_RELATED_TO_DTO[model]
        return dto_class(**data)
    return get


def _update_method(model: Type[SQLAlchemyModel]) -> Callable:
    async def update(self, id: int, dto: TypeDTO) -> TypeDTO:
        values: dict = dto.model_dump()
        values.pop('id')
        stmt = (
            sql.update(model)
            .where(model.id == id)
            .values(**values)
            .returning(model)
        )
        result = await self.session.execute(stmt)
        updated_entity = result.scalar_one()
        if not updated_entity:
            raise ObjectDoesNotExistException(model.__name__, object_id=id)
        dto_class = MODELS_RELATED_TO_DTO[model]
        return dto_class(**updated_entity.as_dict())
    return update


def _delete_method(model: Type[SQLAlchemyModel]) -> Callable:
    async def delete(self, id: int) -> bool:
        stmt = sql.select(model).where(model.id == id)
        result = await self.session.execute(stmt)
        entity = result.scalar_one()
        if not entity:
            raise ObjectDoesNotExistException(model.__name__, object_id=id)
        await self.session.delete(entity)
        return True
    return delete


def _query_executor() -> Callable:
    async def execute_query(
        self,
        *args,
        first: bool = False,
        **kwargs,
    ) -> list[tuple[Any]] | tuple[Any]:
        stmt = self._construct_select_query(*args, **kwargs)
        result = await self.session.execute(stmt)
        if first:
            return result.first()  # type: ignore
        return result.all()  # type: ignore
    return execute_query


def _select_query_constructor(model: Type[SQLAlchemyModel]):
    def construct_select_query(
        self,
        fields: list[SelectedFields],
        **queries,
    ) -> sql.Select:
        object_id = queries.get('id', None)
        _fields = fields[0].fields if len(fields) > 0 else raise_exc(
            Exception('Fields not selected'),
        )
        fields_to_select = [getattr(model, f) for f in _fields]
        offset = queries.get('offset', None)
        limit = queries.get('limit', None)
        stmt = sql.select(*fields_to_select)
        if object_id is not None:
            stmt = stmt.where(model.id == object_id)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return stmt
    return construct_select_query


def _models_to_join(fields: list[SelectedFields]) -> tuple[bool, bool, bool]:
    """
    Returns bool values for models that need to join from SelectedFields:

    `(join_user, join_product, join_review)`
    """
    join_user: bool = False
    join_product: bool = False
    join_review: bool = False
    for field in fields:
        if field.owner.lower() in Entity.USER + 's':
            join_user = True
        elif field.owner.lower() in Entity.PRODUCT + 's':
            join_product = True
        elif field.owner.lower() in Entity.REVIEW + 's':
            join_review = True
    return join_user, join_product, join_review
