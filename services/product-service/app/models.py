from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ----------------------------
# Create Product
# ----------------------------
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: Optional[str] = None
    image_url: Optional[str] = None


# ----------------------------
# Update Product
# ----------------------------
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    image_url: Optional[str] = None


# ----------------------------
# Product Response
# ----------------------------
class ProductResponse(BaseModel):
    id: str  # ✅ FIX: MongoDB ObjectId → string
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ----------------------------
# Stock Update
# ----------------------------
class StockUpdate(BaseModel):
    quantity: int = Field(..., ge=0)
    operation: str = Field(..., pattern="^(add|subtract|set)$")
