from kafka import KafkaProducer
import json
from datetime import datetime
from app.config import settings

class EventProducer:
    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[settings.KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                request_timeout_ms=5000,
                max_block_ms=5000
            )
            print("✅ Kafka producer initialized successfully")
        except Exception as e:
            print(f"⚠️ Kafka not available: {e}")
            self.producer = None
    
    def publish_user_event(self, event_type: str, user_data: dict):
        """Publish user events to Kafka"""
        if self.producer is None:
            print(f"⚠️ Kafka unavailable. Event not published: {event_type}")
            return
        
        try:
            event = {
                "event_type": event_type,
                "data": user_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.producer.send("user-events", value=event)
            self.producer.flush()
            print(f"📤 Published event: {event_type}")
        except Exception as e:
            print(f"❌ Failed to publish event: {e}")

# Create instance
event_producer = EventProducer()