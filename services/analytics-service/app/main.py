from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Optional
import os

app = FastAPI(
    title="Analytics Service",
    description="Event Analytics & Reporting",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@mongodb:27017/")
client = MongoClient(MONGO_URI)
db = client.shopstream
analytics = db.analytics_data

@app.get("/")
def health_check():
    return {
        "service": "analytics-service",
        "status": "healthy",
        "port": 8004
    }

@app.get("/analytics/events")
def get_events(
    topic: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get recent events with optional filters"""
    query = {}
    
    if topic:
        query["topic"] = topic
    if event_type:
        query["event_type"] = event_type
    
    events = list(
        analytics.find(query, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )
    
    # Convert datetime to string
    for event in events:
        if "timestamp" in event and isinstance(event["timestamp"], datetime):
            event["timestamp"] = event["timestamp"].isoformat()
        if "processed_at" in event and isinstance(event["processed_at"], datetime):
            event["processed_at"] = event["processed_at"].isoformat()
    
    return {
        "events": events,
        "count": len(events),
        "filters": {"topic": topic, "event_type": event_type}
    }

@app.get("/analytics/summary")
def get_summary():
    """Get overall analytics summary"""
    total_events = analytics.count_documents({})
    
    # Count by topic
    topics = {}
    for topic in ["user-events", "product-events", "order-events"]:
        topics[topic] = analytics.count_documents({"topic": topic})
    
    # Events in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_events = analytics.count_documents({
        "timestamp": {"$gte": yesterday}
    })
    
    # Event type distribution
    pipeline = [
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    event_types = list(analytics.aggregate(pipeline))
    
    return {
        "total_events": total_events,
        "by_topic": topics,
        "last_24_hours": recent_events,
        "event_types": {item["_id"]: item["count"] for item in event_types if item["_id"]}
    }

@app.get("/analytics/users/stats")
def user_stats():
    """User registration statistics"""
    pipeline = [
        {"$match": {"topic": "user-events", "event_type": "USER_REGISTERED"}},
        {"$group": {
            "_id": None,
            "total_registrations": {"$sum": 1}
        }}
    ]
    
    result = list(analytics.aggregate(pipeline))
    total_reg = result[0]["total_registrations"] if result else 0
    
    # Registrations per day (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    pipeline_daily = [
        {"$match": {
            "topic": "user-events",
            "event_type": "USER_REGISTERED",
            "timestamp": {"$gte": seven_days_ago}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    daily_reg = list(analytics.aggregate(pipeline_daily))
    
    # Login count
    login_count = analytics.count_documents({
        "topic": "user-events",
        "event_type": "USER_LOGIN"
    })
    
    return {
        "total_registrations": total_reg,
        "total_logins": login_count,
        "daily_registrations_last_7_days": {item["_id"]: item["count"] for item in daily_reg}
    }

@app.get("/analytics/orders/stats")
def order_stats():
    """Order statistics"""
    # Total orders
    total_orders = analytics.count_documents({
        "topic": "order-events",
        "event_type": "ORDER_CREATED"
    })
    
    # Total revenue
    pipeline_revenue = [
        {"$match": {"topic": "order-events", "event_type": "ORDER_CREATED"}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$data.total"}
        }}
    ]
    
    revenue_result = list(analytics.aggregate(pipeline_revenue))
    total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
    
    # Completed orders
    completed_orders = analytics.count_documents({
        "topic": "order-events",
        "event_type": "ORDER_COMPLETED"
    })
    
    # Orders by status
    pipeline_status = [
        {"$match": {"topic": "order-events"}},
        {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
    ]
    
    status_dist = list(analytics.aggregate(pipeline_status))
    
    # Average order value
    avg_order = total_revenue / total_orders if total_orders > 0 else 0
    
    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "total_revenue": round(total_revenue, 2),
        "average_order_value": round(avg_order, 2),
        "order_events": {item["_id"]: item["count"] for item in status_dist}
    }

@app.get("/analytics/products/stats")
def product_stats():
    """Product statistics"""
    total_products = analytics.count_documents({
        "topic": "product-events",
        "event_type": "PRODUCT_ADDED"
    })
    
    # Most popular products (from order events)
    pipeline = [
        {"$match": {"topic": "order-events", "event_type": "ORDER_CREATED"}},
        {"$unwind": "$data.items"},
        {"$group": {
            "_id": "$data.items.product_name",
            "total_quantity": {"$sum": "$data.items.quantity"},
            "total_revenue": {"$sum": "$data.items.subtotal"}
        }},
        {"$sort": {"total_quantity": -1}},
        {"$limit": 10}
    ]
    
    popular_products = list(analytics.aggregate(pipeline))
    
    return {
        "total_products_added": total_products,
        "popular_products": [
            {
                "product_name": item["_id"],
                "quantity_sold": item["total_quantity"],
                "revenue": round(item["total_revenue"], 2)
            }
            for item in popular_products
        ]
    }

@app.get("/analytics/timeline")
def get_timeline(hours: int = Query(24, ge=1, le=168)):
    """Get event timeline for last N hours"""
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_time}}},
        {"$group": {
            "_id": {
                "hour": {"$dateToString": {"format": "%Y-%m-%d %H:00", "date": "$timestamp"}},
                "topic": "$topic"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.hour": 1}}
    ]
    
    results = list(analytics.aggregate(pipeline))
    
    # Organize by hour
    timeline = {}
    for item in results:
        hour = item["_id"]["hour"]
        topic = item["_id"]["topic"]
        if hour not in timeline:
            timeline[hour] = {}
        timeline[hour][topic] = item["count"]
    
    return {
        "period_hours": hours,
        "timeline": timeline
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)