# app/kafka_producer.py
import os
import json
from kafka import KafkaProducer

class EventProducer:
    def __init__(self):
        broker = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.producer = KafkaProducer(
            bootstrap_servers=[broker],
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )

    def send(self, topic: str, value: dict):
        self.producer.send(topic, value)
        self.producer.flush()

event_producer = None  # <-- mos e krijo këtu

def get_producer():
    global event_producer
    if event_producer is None:
        event_producer = EventProducer()
    return event_producer
