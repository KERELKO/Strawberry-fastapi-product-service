from fastapi import FastAPI

import strawberry
from strawberry.fastapi import GraphQLRouter

from src.common.db.sqlalchemy.config import db
from src.common.graphql.query import Query
from src.common.graphql.mutations import Mutation
from src.common.middlewares import ExecutingTimeMiddleware
from src.common.settings import config


def init_db_tables():
    import asyncio
    asyncio.run(db.create())


def graphql_app() -> GraphQLRouter:
    schema = strawberry.Schema(query=Query, mutation=Mutation)
    graphql: GraphQLRouter = GraphQLRouter(schema)

    return graphql


def fastapi_app() -> FastAPI:
    app = FastAPI(**config.app_config)
    app.include_router(graphql_app(), prefix='/graphql')

    # Middlewares
    app.add_middleware(ExecutingTimeMiddleware)

    return app
