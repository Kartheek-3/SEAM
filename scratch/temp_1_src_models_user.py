from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "John Doe",
                "email": "john.doe@example.com"
            }
        }