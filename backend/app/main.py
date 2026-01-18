import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import auth, products, ecommerce, profile
from app.db.session import engine


# logger-configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# setup fastapi lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started.")
    try:
        with engine.connect() as connection:
            logger.info("DB connected successfully.")
    except Exception as e:
        logger.error("Error to connect DB.", str(e))

    yield  # the node point (BEFORE_block: run at application startup, AFTER_block: run at application shutdoen)
    logger.info("Application Shuted down.")

    # db connection close
    engine.dispose()
    logger.info("DB connection closed.")


app = FastAPI(
    title="Sellphone API",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",  # For Local Development
    "http://127.0.0.1:5173",  # For Local Development
    "https://sellphoneind.vercel.app",  # THIS IS ACTUAL VERCEL OR MAIN DOMAIN
]

# CORS Configuration (Essential for React Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(ecommerce.router, prefix="/api/v1/shop", tags=["E-commerce"])
app.include_router(profile.router, prefix="/api/v1/user", tags=["User Profile"])
