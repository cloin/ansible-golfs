# mqtt_module.py
from aiomqtt import Client as AsyncMqttClient
import json
import logging

class MQTTClient:
    def __init__(self, broker_address, topic_prefix):
        self.hostname = broker_address.split(':')[0]
        self.port = int(broker_address.split(':')[1]) if ':' in broker_address else 1883
        self.topic_prefix = topic_prefix
        self.client = AsyncMqttClient(hostname=self.hostname, port=self.port)

    async def connect(self):
        await self.client.__aenter__()

    async def publish(self, topic, message):
        if self.client:
            full_topic = f"{self.topic_prefix}/{topic}"
            logging.info(f"Publishing to MQTT topic {full_topic}: {json.dumps(message)}")
            await self.client.publish(full_topic, json.dumps(message).encode())

    async def subscribe_to_commands(self, command_handler, ble_device):
        if self.client:
            command_topic = f"{self.topic_prefix}/command"
            logging.info(f"Subscribing to command topic {command_topic}")
            await self.client.subscribe(command_topic)
            logging.info(f"Subscribed to {command_topic}")
            async for message in self.client.messages:
                logging.info(f"Received MQTT message on {command_topic}: {message.payload.decode()}")
                try:
                    await command_handler(json.loads(message.payload.decode()), ble_device)
                except Exception as e:
                    logging.error(f"Error handling command: {e}")

    async def disconnect(self):
        if self.client:
            await self.client.__aexit__(None, None, None)
