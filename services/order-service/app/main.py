
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import requests
from datetime import datetime

from app.models import OrderCreate, PaymentCreate
from app.database import db
from app.kafka_producer import get_producer
from app.config import settings

app = FastAPI(
    title="Order Service",
    description="Order Processing & Payment Integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"service": "order-service", "status": "healthy", "port": 8003}

# ------------------ CREATE ORDER ------------------
@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate):
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # 1) verify user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (order.user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="User not found")

        # 2) validate products + total
        total = 0
        order_details = []

        for item in order.items:
            try:
                # product
                r = requests.get(f"{settings.PRODUCT_SERVICE_URL}/products/{item.product_id}", timeout=5)
                if r.status_code == 404:
                    raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
                if r.status_code != 200:
                    raise HTTPException(status_code=502, detail="Product Service error")
                product = r.json()

                # inventory
                inv_r = requests.get(f"{settings.PRODUCT_SERVICE_URL}/inventory/{item.product_id}", timeout=5)
                inv = inv_r.json()
                if inv["available"] < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for {product['name']}. Available: {inv['available']}"
                    )

                subtotal = product["price"] * item.quantity
                total += subtotal
                order_details.append({
                    "product_id": item.product_id,
                    "product_name": product["name"],
                    "quantity": item.quantity,
                    "price": product["price"],
                    "subtotal": subtotal
                })

            except requests.exceptions.RequestException:
                raise HTTPException(status_code=503, detail="Product Service unavailable")

        # 3) create order
        cursor.execute(
            """
            INSERT INTO orders (user_id, status, total_amount)
            OUTPUT INSERTED.id, INSERTED.created_at
            VALUES (%s, %s, %s)
            """,
            (order.user_id, "pending", total)
        )
        res = cursor.fetchone()
        order_id = res[0]
        created_at = res[1]

        # 4) transaction
        cursor.execute(
            """
            INSERT INTO transactions (order_id, user_id, amount, transaction_type, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (order_id, order.user_id, total, "order_creation", "completed")
        )

        conn.commit()

        # 5) reserve inventory (best-effort)
        for item in order.items:
            try:
                requests.post(
                    f"{settings.PRODUCT_SERVICE_URL}/inventory/{item.product_id}/reserve",
                    params={"quantity": item.quantity},
                    timeout=5
                )
            except:
                pass

        # 6) publish kafka event
        event_producer.publish_order_event("ORDER_CREATED", {
            "order_id": order_id,
            "user_id": order.user_id,
            "items": order_details,
            "total": float(total),
            "status": "pending",
            "created_at": str(created_at)
        })

        return {
            "order_id": order_id,
            "status": "pending",
            "total": float(total),
            "items": order_details,
            "created_at": str(created_at),
            "message": "Order created successfully"
        }

# ------------------ LIST ORDERS ------------------
@app.get("/orders")
def list_orders(user_id: Optional[int] = None, status: Optional[str] = None):
    with db.get_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT id, user_id, status, total_amount, created_at FROM orders"
        conditions = []
        params = []

        if user_id is not None:
            conditions.append("user_id = %s")
            params.append(user_id)
        if status is not None:
            conditions.append("status = %s")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"

        cursor.execute(query, params if params else None)
        rows = cursor.fetchall()

        return {
            "orders": [
                {"id": o[0], "user_id": o[1], "status": o[2], "total": float(o[3]), "created_at": str(o[4])}
                for o in rows
            ],
            "count": len(rows)
        }

# ------------------ GET ORDER ------------------
@app.get("/orders/{order_id}")
def get_order(order_id: int):
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, status, total_amount, created_at FROM orders WHERE id = %s",
            (order_id,)
        )
        o = cursor.fetchone()
        if not o:
            raise HTTPException(status_code=404, detail="Order not found")
        return {"id": o[0], "user_id": o[1], "status": o[2], "total": float(o[3]), "created_at": str(o[4])}

# ------------------ UPDATE STATUS ------------------
@app.put("/orders/{order_id}/status")
def update_order_status(order_id: int, new_status: str):
    valid = ["pending", "processing", "completed", "canceled"]
    if new_status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = %s, updated_at = GETDATE() WHERE id = %s", (new_status, order_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        conn.commit()

    event_producer.publish_order_event(f"ORDER_{new_status.upper()}", {"order_id": order_id, "status": new_status})
    return {"message": f"Order status updated to {new_status}"}

# ------------------ PAYMENTS ------------------
@app.post("/payments", status_code=status.HTTP_201_CREATED)
def process_payment(payment: PaymentCreate):
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, status, total_amount FROM orders WHERE id = %s", (payment.order_id,))
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if order[1] != "pending":
            raise HTTPException(status_code=400, detail=f"Order not pending. Current: {order[1]}")
        if abs(payment.amount - float(order[2])) > 0.01:
            raise HTTPException(status_code=400, detail="Payment amount does not match order total")

        txid = f"TXN_{payment.order_id}_{int(datetime.now().timestamp())}"

        cursor.execute(
            """
            INSERT INTO payments (order_id, payment_method, amount, status, transaction_id)
            OUTPUT INSERTED.id, INSERTED.created_at
            VALUES (%s, %s, %s, %s, %s)
            """,
            (payment.order_id, payment.payment_method, payment.amount, "completed", txid)
        )
        res = cursor.fetchone()
        payment_id = res[0]
        created_at = res[1]

        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", ("completed", payment.order_id))
        conn.commit()

        event_producer.publish_order_event("ORDER_COMPLETED", {
            "order_id": payment.order_id,
            "payment_id": payment_id,
            "payment_method": payment.payment_method,
            "amount": float(payment.amount),
            "transaction_id": txid
        })

        return {
            "payment_id": payment_id,
            "order_id": payment.order_id,
            "status": "completed",
            "transaction_id": txid,
            "created_at": str(created_at),
            "message": "Payment processed successfully"
        }

