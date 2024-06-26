import sqlalchemy as sql

from src.common.db.sqlalchemy.extensions import sqlalchemy_repo_extended
from src.common.db.sqlalchemy.models import Review
from src.common.db.sqlalchemy.base import BaseSQLAlchemyRepository
from src.products.dto import ReviewDTO


@sqlalchemy_repo_extended(query_executor=False)
class SQLAlchemyReviewRepository(BaseSQLAlchemyRepository):
    class Meta:
        model = Review

    def _construct_select_query(self, fields: list[str], **queries) -> sql.Select:
        fields_to_select = [getattr(Review, f) for f in fields]
        review_id = queries.get('id', None)
        product_id = queries.get('product_id', None)
        user_id = queries.get('user_id', None)
        offset = queries.get('offset', None)
        limit = queries.get('limit', None)
        stmt = sql.select(*fields_to_select)

        if review_id is not None:
            return stmt.where(Review.id == review_id)
        elif user_id is not None:
            stmt = stmt.where(Review.user_id == user_id)
        elif product_id is not None:
            stmt = stmt.where(Review.product_id == product_id)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return stmt

    async def get_list(
        self,
        fields: list[str],
        offset: int = 0,
        limit: int = 20,
        product_id: int | None = None,
        user_id: int | None = None,
    ) -> list[ReviewDTO]:
        list_values = await self._execute_query(
            fields=fields,
            offset=offset,
            limit=limit,
            product_id=product_id,
            user_id=user_id,
        )
        dto_list = []
        for values in list_values:
            data = {f: v for f, v in zip(fields, values)}
            dto_list.append(ReviewDTO(**data))
        return dto_list
