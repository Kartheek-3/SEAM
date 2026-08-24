from fastapi import APIRouter
from . import app

router = APIRouter()

@router.get("/products/")
async def read_products():
    return [{"id": 1, "name": "Product 1", "price": 10.99}, {"id": 2, "name": "Product 2", "price": 9.99}]

@router.post("/products/")
async def create_product(product: dict):
    return product