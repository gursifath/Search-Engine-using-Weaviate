import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import config, logger
from routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Search Engine Chat API...")
    logger.info(f"Debug mode: {config.DEBUG}")
    logger.info(f"OpenAI API configured: {'Yes' if config.OPENAI_API_KEY else 'No'}")
    logger.info(f"Weaviate configured: {'Yes' if config.WEAVIATE_URL else 'No'}")

    try:
        from client import openai_client
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")

    yield

    logger.info("Shutting down Search Engine Chat API...")

app = FastAPI(
    title="Search Engine Chat API",
    version="1.0.0",
    description="FastAPI backend for AI-powered search engine with chat functionality",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# FastAPI app is defined above and can be imported by other modules
# Use run_server.py to start the server