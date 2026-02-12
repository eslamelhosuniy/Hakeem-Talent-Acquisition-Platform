from fastapi import FastAPI
from routes import base
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from routes.cv_routes import router as cv_router


app = FastAPI(
    title="AI Talent Platform",
    description="AI-powered talent platform for smart hiring and candidate matching",
    version="0.1.0",
)


async def startup_span():
    settings = get_settings()

    # # PostgreSQL connection
    # postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"

    # app.db_engine = create_async_engine(postgres_conn)
    # app.db_client = sessionmaker(
    #     app.db_engine, class_=AsyncSession, expire_on_commit=False
    # )

    # llm_provider_factory = LLMProviderFactory(settings)
    # vectordb_provider_factory = VectorDBProviderFactory(settings)

    # # Generation client (for resume analysis, job matching, NLP)
    # app.generation_client = llm_provider_factory.create(
    #     provider=settings.GENERATION_BACKEND
    # )
    # app.generation_client.set_generation_model(model_id=settings.GENERATION_MODEL_ID)

    # # Embedding client (for semantic search)
    # app.embedding_client = llm_provider_factory.create(
    #     provider=settings.EMBEDDING_BACKEND
    # )
    # app.embedding_client.set_embedding_model(
    #     model_id=settings.EMBEDDING_MODEL_ID,
    #     embedding_size=settings.EMBEDDING_MODEL_SIZE,
    # )

    # # Vector DB client (for candidate/job search)
    # app.vectordb_client = vectordb_provider_factory.create(
    #     provider=settings.VECTOR_DB_BACKEND
    # )
    # app.vectordb_client.connect()

    # Template parser for prompts
    app.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG,
    )


async def shutdown_span():
    # await app.db_engine.dispose()
    pass


app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)

# Routes
app.include_router(base.main_router)
app.include_router(base.base_router)
app.include_router(cv_router)

