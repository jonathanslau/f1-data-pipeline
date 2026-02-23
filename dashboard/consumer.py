"""Poll-based Kafka consumer wrapper."""

import json
from confluent_kafka import Consumer, KafkaError


class TelemetryConsumer:
    """Non-blocking Kafka consumer that drains available messages each poll cycle."""

    def __init__(self, bootstrap_servers, topics, group_id="dashboard"):
        self._consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        })
        self._consumer.subscribe(topics)

    def poll_batch(self, max_messages=200, timeout=0.0):
        """Poll for up to max_messages. Returns two lists: (telemetry_msgs, lap_msgs)."""
        telemetry = []
        laps = []

        for _ in range(max_messages):
            msg = self._consumer.poll(timeout)
            if msg is None:
                break
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                break

            topic = msg.topic()
            try:
                value = json.loads(msg.value().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            if "telemetry" in topic:
                telemetry.append(value)
            elif "laps" in topic:
                laps.append(value)

        return telemetry, laps

    def close(self):
        self._consumer.close()
