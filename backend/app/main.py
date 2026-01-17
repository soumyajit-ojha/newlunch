from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, products, ecommerce

app = FastAPI()

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

@app.get("/new")
def read_item():
    return {"message":"hello there"}