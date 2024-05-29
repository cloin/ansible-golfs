import asyncio
import argparse
import logging
import os
from mqtt_module import MQTTClient
from ble_module import BLEDevice
from data_processing import process_notification, handle_command

def parse_args():
    parser = argparse.ArgumentParser(description='BLE and MQTT Integration Application')
    parser.add_argument('-m', '--mqtt-broker', default=os.getenv('MQTT_BROKER'), required=not os.getenv('MQTT_BROKER'), help='MQTT broker address')
    parser.add_argument('-g', '--golfball', default=f"{os.getenv('BLE_ID')}:{os.getenv('GOLF_BALL', 'golfball1')}", required=not os.getenv('BLE_ID'), help='Device name and friendly name pair, formatted as device_name:friendly_name')
    return parser.parse_args()

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    setup_logging()
    args = parse_args()

    device_name, friendly_name = args.golfball.split(':')

    mqtt_client = MQTTClient(args.mqtt_broker, "ansible-golfs")
    ble_device = BLEDevice(device_name)

    try:
        await mqtt_client.connect()
        logging.info("Connected to MQTT broker")

        while True:
            try:
                await ble_device.connect_and_setup()
                logging.info("BLE device connected and set up")

                logging.info("Subscribing to MQTT commands")
                asyncio.create_task(mqtt_client.subscribe_to_commands(handle_command, ble_device))
                logging.info("Subscribed to MQTT commands")

                logging.info("About to call subscribe_to_notifications")
                await ble_device.subscribe_to_notifications(process_notification, mqtt_client, "golfball")
                logging.info("Subscribed to BLE notifications")

                # Run indefinitely until disconnected
                while True:
                    if not ble_device.client.is_connected:
                        logging.info("BLE device disconnected, attempting to reconnect...")
                        break
                    await asyncio.sleep(1)

            except Exception as e:
                logging.error(f"Exception occurred: {e}")
                logging.info("Retrying connection to BLE device...")

            # Sleep before retrying to avoid spamming connection attempts
            await asyncio.sleep(5)

    except Exception as e:
        logging.error(f"Exception occurred: {e}")

    finally:
        await ble_device.disconnect()
        logging.info("BLE device disconnected")
        await mqtt_client.disconnect()
        logging.info("MQTT client disconnected")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application exited by user")
