from kafka import KafkaProducer
import json
from datetime import datetime
from app.config import settings

class EventProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=[settings.KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
    
    def publish_product_event(self, event_type: str, product_data: dict):
        """Publish product events to Kafka"""
        event = {
            "event_type": event_type,
            "data": product_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.producer.send("product-events", value=event)
        self.producer.flush()
        print(f"📤 Published event: {event_type}")

event_producer = EventProducer()
