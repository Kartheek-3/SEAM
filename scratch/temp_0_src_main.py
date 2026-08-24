from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Product(BaseModel):
    id: int
    name: str
    price: float

@app.get("/products/")
async def read_products():
    return [{"id": 1, "name": "Product 1", "price": 10.99}, {"id": 2, "name": "Product 2", "price": 9.99}]

@app.post("/products/")
async def create_product(product: Product):
    return product