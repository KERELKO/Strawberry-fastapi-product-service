from functools import cache
from typing import Type, TypeVar
import logging

import punq

from src.products.graphql.resolvers.reviews import StrawberryReviewResolver
from src.products.repositories.base import (
    AbstractReviewRepository,
    AbstractProductUnitOfWork,
    AbstractProductRepository,
    AbstractReviewUnitOfWork,
)
from src.products.repositories.sqlalchemy.products.repo import SQLAlchemyProductRepository
from src.products.repositories.sqlalchemy.products.uow import SQLAlchemyProductUnitOfWork
from src.products.repositories.sqlalchemy.reviews.repo import (
    SQLAlchemyAggregatedReviewRepository,
)
from src.products.repositories.sqlalchemy.reviews.uow import SQLAlchemyReviewUnitOfWork
from src.products.services.reviews import ReviewService
from src.users.repositories.base import AbstractUserRepository, AbstractUserUnitOfWork
from src.users.repositories.sqlalchemy.repo import SQLAlchemyUserRepository
from src.users.repositories.sqlalchemy.uow import SQLAlchemyUserUnitOfWork


ABC = TypeVar('ABC')
Impl = TypeVar('Impl')


class Container:
    @staticmethod
    def get() -> punq.Container:
        return Container._init()

    @staticmethod
    def resolve(base_cls: Type[ABC]) -> Impl:
        return Container.get().resolve(base_cls)

    @cache
    @staticmethod
    def _init() -> punq.Container:
        container = punq.Container()

        logger = logging.getLogger('Logger')
        container.register(logging.Logger, instance=logger)

        container.register(AbstractUserRepository, SQLAlchemyUserRepository)
        container.register(AbstractUserUnitOfWork, SQLAlchemyUserUnitOfWork)

        container.register(AbstractReviewRepository, SQLAlchemyAggregatedReviewRepository)
        container.register(AbstractReviewUnitOfWork, SQLAlchemyReviewUnitOfWork)

        container.register(AbstractProductRepository, SQLAlchemyProductRepository)
        container.register(AbstractProductUnitOfWork, SQLAlchemyProductUnitOfWork)

        container.register(ReviewService)
        container.register(StrawberryReviewResolver)

        return container
