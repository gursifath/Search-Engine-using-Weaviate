"""
Script to run the FastAPI backend server
"""

if __name__ == "__main__":
    import uvicorn
    from config import config
    import logging

    logger = logging.getLogger(__name__)

    print("🚀 Starting Search Engine Chat API...")
    print(f"📍 API will be available at: http://{config.API_HOST}:{config.API_PORT}")
    print(f"📚 API docs will be available at: http://{config.API_HOST}:{config.API_PORT}/docs")
    print("🔧 Make sure to set your OPENAI_API_KEY in a .env file")

    logger.info("Server startup initiated")

    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )