# ble_module.py
from bleak import BleakScanner, BleakClient
import asyncio
import logging

class BLEDevice:
    CHARACTERISTIC_READY_UUID = "00000000-0000-1000-8000-00805f9b34f1"  # 'Ready' characteristic UUID
    BATTERY_LEVEL_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb"  # Battery Level characteristic UUID
    CHARACTERISTICS_OF_INTEREST = {
        "00000000-0000-1000-8000-00805f9b34f3": "ballRollCount",
        "00000000-0000-1000-8000-00805f9b34f4": "Velocity",
        "00000000-0000-1000-8000-00805f9b34f1": "Ready",
        "0d79161c-4469-4870-aceb-3e563875a0b7": "ballState"
    }

    def __init__(self, device_name):
        self.device_name = device_name
        self.client = None

    async def connect_and_setup(self):
        device = await self.discover_device(self.device_name)
        if device is None:
            raise Exception("Device not found")
        self.client = BleakClient(device.address)
        await self.client.connect()
        logging.info(f"Connected to BLE device {self.device_name}")

        # Perform initial write to 'Ready' characteristic to initialize device
        try:
            logging.info(f"Writing to characteristic {self.CHARACTERISTIC_READY_UUID} to set it ready")
            await self.client.write_gatt_char(self.CHARACTERISTIC_READY_UUID, bytearray([0x01]))
            logging.info(f"Successfully wrote to characteristic {self.CHARACTERISTIC_READY_UUID}")
        except Exception as e:
            logging.error(f"Failed to write to characteristic {self.CHARACTERISTIC_READY_UUID}: {e}")

        # Read the battery level on connect
        try:
            battery_level = await self.client.read_gatt_char(self.BATTERY_LEVEL_CHARACTERISTIC_UUID)
            battery_percentage = int(battery_level[0])
            logging.info(f"Battery Level: {battery_percentage}%")
        except Exception as e:
            logging.error(f"Failed to read battery level: {e}")

    async def discover_device(self, device_name):
        devices = await BleakScanner.discover()
        for device in devices:
            if device.name == device_name:
                return device
        return None

    async def subscribe_to_notifications(self, handler, mqtt_client, friendly_name):
        logging.info("Entered subscribe_to_notifications method")
        # Subscribe to notifications for each characteristic of interest
        try:
            logging.info("Discovering services and characteristics...")
            await self.client.get_services()
            for service in self.client.services:
                for characteristic in service.characteristics:
                    logging.info(f"Discovered characteristic: {characteristic.uuid}")

            for uuid, name in self.CHARACTERISTICS_OF_INTEREST.items():
                try:
                    logging.info(f"Attempting to subscribe to {name} with UUID {uuid}")
                    await self.client.start_notify(uuid, lambda s, d: asyncio.create_task(handler(s, d, mqtt_client, name, self.client)))
                    logging.info(f"Subscribed to notifications for {name} with UUID {uuid}")
                except Exception as e:
                    logging.error(f"Failed to subscribe to {name} with UUID {uuid}: {e}")
        except Exception as e:
            logging.error(f"Error discovering services or subscribing to characteristics: {e}")

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            logging.info(f"Disconnected from BLE device {self.device_name}")
