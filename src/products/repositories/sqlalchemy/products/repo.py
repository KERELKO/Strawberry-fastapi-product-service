from typing import Any

import sqlalchemy as sql

from src.common.db.sqlalchemy.base import BaseSQLAlchemyRepository
from src.common.db.sqlalchemy.extensions import sqlalchemy_repo_extended
from src.common.db.sqlalchemy.models import Product, Review
from src.products.dto import ProductDTO
from src.common.exceptions import ObjectDoesNotExistException


@sqlalchemy_repo_extended(query_executor=False)
class SQLAlchemyProductRepository(BaseSQLAlchemyRepository):
    class Meta:
        model = Product

    def _construct_select_query(
        self,
        fields: list[str],
        **queries,
    ) -> sql.Select:
        product_id = queries.get('id', None)
        review_id = queries.get('review_id', None)
        fields_to_select = [getattr(Product, f) for f in fields]
        offset = queries.get('offset', None)
        limit = queries.get('limit', None)
        stmt = sql.select(*fields_to_select)

        if product_id is not None:
            stmt = stmt.where(Product.id == product_id)
        elif review_id is not None:
            stmt = self._join_reviews(stmt)
            stmt = stmt.where(Review.id == review_id)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return stmt

    async def get_by_review_id(self, review_id: int, fields: list[str]) -> ProductDTO:
        values = await self._execute_query(fields=fields, review_id=review_id, first=True)
        if not values:
            raise ObjectDoesNotExistException('Product')
        data: dict[str, Any] = {f: v for f, v in zip(fields, values)}
        return ProductDTO(**data)

    async def get_list(
        self,
        fields: list[str],
        offset: int = 0,
        limit: int = 20,
    ) -> list[ProductDTO]:
        list_values = await self._execute_query(fields=fields, offset=offset, limit=limit)
        dto_list = []
        for values in list_values:
            data = {f: v for f, v in zip(fields, values)}
            dto_list.append(ProductDTO(**data))
        return dto_list
