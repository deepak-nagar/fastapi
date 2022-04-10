from pydantic import BaseModel
from product.models import Product


class Product(BaseModel):
    name: str
    desc: str
    price: int


class DisplayProduct(BaseModel):
    id: int
    desc: str

    class Config:
        orm_mode = True


class Seller(BaseModel):
    username: str
    email: str
    password: str
