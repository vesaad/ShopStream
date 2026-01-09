from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from app.models import ProductCreate, ProductUpdate, ProductResponse, StockUpdate
from app.database import mongodb
from app.kafka_producer import event_producer

app = FastAPI(
    title="Product Service",
    description="Product Management Service (MongoDB)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Helpers
# ----------------------------
def mongo_to_product(doc) -> ProductResponse:
    return ProductResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description"),
        price=float(doc["price"]),
        stock=doc["stock"],
        category=doc["category"],
        image_url=doc.get("image_url"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )

# ----------------------------
# Health
# ----------------------------
@app.get("/")
def health_check():
    return {"service": "product-service", "status": "healthy"}

# ----------------------------
# Products
# ----------------------------
@app.get("/products", response_model=List[ProductResponse])
def list_products():
    products = mongodb.products.find()
    return [mongo_to_product(p) for p in products]


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    data = product.dict()
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = None

    result = mongodb.products.insert_one(data)

    event_producer.publish_product_event(
        "PRODUCT_CREATED",
        {"id": str(result.inserted_id), "name": product.name}
    )

    return mongo_to_product({**data, "_id": result.inserted_id})


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    try:
        product = mongodb.products.find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid product ID")

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return mongo_to_product(product)
