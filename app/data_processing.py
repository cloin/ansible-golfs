# data_processing.py is responsible for processing the data received from the BLE device and sending it to the MQTT broker.
import logging
import json
import asyncio
from ble_module import BLEDevice

CHARACTERISTICS = {
    "00000000-0000-1000-8000-00805f9b34f3": "ballRollCount",
    "00000000-0000-1000-8000-00805f9b34f4": "Velocity",
    "00000000-0000-1000-8000-00805f9b34f1": "Ready",
    "0d79161c-4469-4870-aceb-3e563875a0b7": "ballState"
}

BALL_STATE_ENUM = [
    "ST_READY",
    "ST_PUTT_STARTED",
    "ST_MAGNET_STOP",
    "ST_PUTT_STOPPING",
    "ST_BALL_STOPPED",
    "ST_PUTT_COMPLETE",
    "ST_PUTT_NOT_COUNTED",
    "ST_PUTT_CONNECT"
]

st_magnet_stop_encountered = False  # Tracks if ST_MAGNET_STOP was encountered
stroke_counter = 0  # Tracks strokes

async def process_notification(sender, data, mqtt_client, characteristic_name, ble_client):
    global st_magnet_stop_encountered, stroke_counter
    logging.info(f"Notification received from {characteristic_name}: {data}")

    if characteristic_name == "Velocity":
        data_value = data[1] / 10.0  # Convert to ft/sec
    else:
        data_value = data[1] if len(data) > 1 else data[0]

    try:
        if characteristic_name == "ballState":
            state_index = data[0]
            data_value = BALL_STATE_ENUM[state_index] if state_index < len(BALL_STATE_ENUM) else "UNKNOWN_STATE"
            
            if data_value == "ST_PUTT_COMPLETE":
                stroke_counter += 1
            elif data_value == "ST_PUTT_NOT_COUNTED":
                stroke_counter = max(stroke_counter - 1, 0)  # Ensure counter doesn't go below 0
            
            if data_value == "ST_MAGNET_STOP":
                logging.info("ST_MAGNET_STOP detected. The golf ball has landed in the cup.")
                st_magnet_stop_encountered = True
            elif data_value == "ST_PUTT_COMPLETE" and not st_magnet_stop_encountered:
                logging.info("ST_PUTT_COMPLETE detected without ST_MAGNET_STOP. Toggling Ready state to wake the ball.")
                await ble_client.write_gatt_char(BLEDevice.CHARACTERISTIC_READY_UUID, bytearray([0x00]))  # Set Ready to 0
                await asyncio.sleep(0.5)
                await ble_client.write_gatt_char(BLEDevice.CHARACTERISTIC_READY_UUID, bytearray([0x01]))  # Set Ready back to 1

        # Construct and send the MQTT message
        if characteristic_name in ["ballState", "ballRollCount", "Velocity"]:
            message = {"data": data_value, "stroke": stroke_counter}
        else:
            message = {"data": data_value}

        mqtt_topic = f"{characteristic_name}"
        await mqtt_client.publish(mqtt_topic, message)

        logging.info(f"BLE Notification: {characteristic_name} - {json.dumps(message)}")

        # Reset the stroke counter and flag after sending the ST_MAGNET_STOP message
        if data_value == "ST_MAGNET_STOP":
            stroke_counter = 0
            st_magnet_stop_encountered = False

    except Exception as e:
        logging.error(f"Error handling BLE notification for {characteristic_name}: {e}")

async def handle_command(message, ble_device):
    logging.info(f"Received command message: {message}")
    command = message.get('command')
    logging.info(f"Extracted command: {command}")
    if command == 'reset':
        logging.info(f"Handling reset command")
        try:
            await ble_device.client.write_gatt_char(BLEDevice.CHARACTERISTIC_READY_UUID, bytearray([0x01]))
            stroke_counter = 0
            logging.info(f"Successfully reset device with characteristic {BLEDevice.CHARACTERISTIC_READY_UUID}")
        except Exception as e:
            logging.error(f"Failed to reset device: {e}")
