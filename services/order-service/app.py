from fastapi import FastAPI, HTTPException
from bson import ObjectId
from db_mongo import products, inventory
from db_mssql import get_conn
from models import CheckoutRequest

app = FastAPI(title="ShopStream Order Service")

def oid(x: str) -> ObjectId:
    try:
        return ObjectId(x)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid product_id: {x}")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/checkout")
def checkout(payload: CheckoutRequest):
    total = 0.0
    line_items = []

    # 1) Validate products + reserve inventory
    for item in payload.items:
        pid = oid(item.product_id)
        prod = products.find_one({"_id": pid})
        if not prod:
            raise HTTPException(status_code=404, detail="Product not found")

        res = inventory.update_one(
            {"product_id": pid, "quantity": {"$gte": item.quantity}},
            {"$inc": {"quantity": -item.quantity, "reserved": item.quantity}}
        )

        if res.matched_count != 1:
            raise HTTPException(status_code=409, detail=f"Not enough stock for {prod['name']}")

        price = float(prod["price"])
        total += price * item.quantity
        line_items.append((str(pid), item.quantity, price))

    # 2) Insert order into SQL Server
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO dbo.Orders(UserId, Total) OUTPUT INSERTED.Id VALUES (?, ?)",
            payload.user_id, total
        )
        order_id = cur.fetchone()[0]

        for (product_id, qty, unit_price) in line_items:
            cur.execute(
                "INSERT INTO dbo.OrderItems(OrderId, ProductId, Quantity, UnitPrice) "
                "VALUES (?, ?, ?, ?)",
                order_id, product_id, qty, unit_price
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

    return {
        "order_id": order_id,
        "total": round(total, 2),
        "items": line_items
    }

