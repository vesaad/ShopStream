from pydantic import BaseModel, Field
from typing import List

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)

class CheckoutRequest(BaseModel):
    user_id: str
    items: List[CartItem]
