
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItem]

class PaymentCreate(BaseModel):
    order_id: int
    payment_method: str
    amount: float = Field(..., gt=0)
