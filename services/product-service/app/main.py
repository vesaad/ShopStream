from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from app.models import ProductCreate, ProductUpdate, ProductResponse, StockUpdate
from app.database import db
from app.kafka_producer import event_producer

app = FastAPI(
    title="Product Service",
    description="Product Management Service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "service": "product-service",
        "status": "healthy",
        "port": 8002
    }

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate):
    """Create a new product"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO products (name, description, price, stock, category, image_url)
                OUTPUT INSERTED.id, INSERTED.name, INSERTED.description, INSERTED.price, 
                       INSERTED.stock, INSERTED.category, INSERTED.image_url, 
                       INSERTED.created_at, INSERTED.updated_at
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (product.name, product.description, product.price, 
                 product.stock, product.category, product.image_url)
            )
            result = cursor.fetchone()
            conn.commit()
            
            product_data = {
                "id": result[0],
                "name": result[1],
                "description": result[2],
                "price": float(result[3]),
                "stock": result[4],
                "category": result[5],
                "image_url": result[6],
                "created_at": str(result[7]),
                "updated_at": str(result[8]) if result[8] else None
            }
            
            event_producer.publish_product_event("PRODUCT_CREATED", product_data)
            
            return ProductResponse(**product_data)
            
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to create product: {str(e)}")

@app.get("/products", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
):
    """List products with filters"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT id, name, description, price, stock, category, image_url, created_at, updated_at FROM products WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        
        if in_stock is not None:
            if in_stock:
                query += " AND stock > 0"
            else:
                query += " AND stock = 0"
        
        query += " ORDER BY created_at DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([skip, limit])
        
        cursor.execute(query, params)
        products = cursor.fetchall()
        
        return [
            ProductResponse(
                id=p[0],
                name=p[1],
                description=p[2],
                price=float(p[3]),
                stock=p[4],
                category=p[5],
                image_url=p[6],
                created_at=p[7],
                updated_at=p[8]
            )
            for p in products
        ]

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    """Get a specific product"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, description, price, stock, category, image_url, created_at, updated_at 
            FROM products WHERE id = ?
            """,
            (product_id,)
        )
        product = cursor.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductResponse(
            id=product[0],
            name=product[1],
            description=product[2],
            price=float(product[3]),
            stock=product[4],
            category=product[5],
            image_url=product[6],
            created_at=product[7],
            updated_at=product[8]
        )

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate):
    """Update a product"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")
        
        update_fields = []
        params = []
        
        if product.name is not None:
            update_fields.append("name = ?")
            params.append(product.name)
        if product.description is not None:
            update_fields.append("description = ?")
            params.append(product.description)
        if product.price is not None:
            update_fields.append("price = ?")
            params.append(product.price)
        if product.stock is not None:
            update_fields.append("stock = ?")
            params.append(product.stock)
        if product.category is not None:
            update_fields.append("category = ?")
            params.append(product.category)
        if product.image_url is not None:
            update_fields.append("image_url = ?")
            params.append(product.image_url)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = GETDATE()")
        params.append(product_id)
        
        query = f"""
            UPDATE products 
            SET {', '.join(update_fields)}
            OUTPUT INSERTED.id, INSERTED.name, INSERTED.description, INSERTED.price, 
                   INSERTED.stock, INSERTED.category, INSERTED.image_url, 
                   INSERTED.created_at, INSERTED.updated_at
            WHERE id = ?
        """
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.commit()
        
        product_data = {
            "id": result[0],
            "name": result[1],
            "description": result[2],
            "price": float(result[3]),
            "stock": result[4],
            "category": result[5],
            "image_url": result[6],
            "created_at": str(result[7]),
            "updated_at": str(result[8]) if result[8] else None
        }
        
        event_producer.publish_product_event("PRODUCT_UPDATED", product_data)
        
        return ProductResponse(**product_data)

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int):
    """Delete a product"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        
        event_producer.publish_product_event("PRODUCT_DELETED", {
            "id": product[0],
            "name": product[1]
        })

@app.patch("/products/{product_id}/stock", response_model=ProductResponse)
def update_stock(product_id: int, stock_update: StockUpdate):
    """Update product stock"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        
        current_stock = result[0]
        
        if stock_update.operation == "add":
            new_stock = current_stock + stock_update.quantity
        elif stock_update.operation == "subtract":
            new_stock = current_stock - stock_update.quantity
            if new_stock < 0:
                raise HTTPException(status_code=400, detail="Insufficient stock")
        else:
            new_stock = stock_update.quantity
        
        cursor.execute(
            """
            UPDATE products 
            SET stock = ?, updated_at = GETDATE()
            OUTPUT INSERTED.id, INSERTED.name, INSERTED.description, INSERTED.price, 
                   INSERTED.stock, INSERTED.category, INSERTED.image_url, 
                   INSERTED.created_at, INSERTED.updated_at
            WHERE id = ?
            """,
            (new_stock, product_id)
        )
        result = cursor.fetchone()
        conn.commit()
        
        product_data = {
            "id": result[0],
            "name": result[1],
            "description": result[2],
            "price": float(result[3]),
            "stock": result[4],
            "category": result[5],
            "image_url": result[6],
            "created_at": str(result[7]),
            "updated_at": str(result[8]) if result[8] else None
        }
        
        event_producer.publish_product_event("STOCK_UPDATED", {
            **product_data,
            "old_stock": current_stock,
            "new_stock": new_stock,
            "operation": stock_update.operation,
            "quantity": stock_update.quantity
        })
        
        return ProductResponse(**product_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
