import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers.v1 import auth, products, ecommerce, profile
from app.db.session import engine
from app.utils.log_config import logger


# setup fastapi lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started.")
    try:
        with engine.connect() as conn:
            logger.info("DB connected successfully.")
    except Exception as e:
        logger.error("Error connecting to DB: %s", e)

    yield  # BEFORE: startup, AFTER: shutdown
    logger.info("Application shut down.")

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    client = request.client.host if request.client else "unknown"
    logger.info(
        "%s %s %s | %s | %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        client,
        duration_ms,
    )
    return response


app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(ecommerce.router, prefix="/api/v1/shop", tags=["E-commerce"])
app.include_router(profile.router, prefix="/api/v1/user", tags=["User Profile"])
