from kafka import KafkaProducer
import json
import os

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")
TOPIC = "product-events"

class EventProducer:
    def __init__(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            print("✅ Kafka producer connected")
        except Exception as e:
            self.producer = None
            print("⚠️ Kafka not available:", e)

    def publish_product_event(self, event_type: str, data: dict):
        if not self.producer:
            print("⚠️ Kafka skipped (producer not ready)")
            return

        try:
            self.producer.send(
                TOPIC,
                {
                    "type": event_type,
                    "data": data,
                },
            )
            self.producer.flush()
        except Exception as e:
            print("⚠️ Kafka publish failed:", e)


# Singleton producer
event_producer = EventProducer()
