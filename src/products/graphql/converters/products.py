from src.products.dto import ProductDTO
from src.products.graphql.schemas.products.queries import Product

from .reviews import StrawberryReviewConverter


class StrawberryProductConverter:
    review_converter: type[StrawberryReviewConverter] = StrawberryReviewConverter

    @classmethod
    def convert(cls, dto: ProductDTO) -> Product:
        reviews = []
        data = dto.model_dump()
        if hasattr(dto, 'reviews'):
            reviews = [cls.review_converter.convert(p) for p in dto.reviews]
            data.pop('reviews')
        product = Product(**data, _reviews=reviews)
        return product
