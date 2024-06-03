"""
BLE Device Characteristics Explorer

This script uses the Bleak library to scan for BLE devices that match a specified name pattern,
then lists all the GATT services, characteristics, and descriptors for the discovered device,
including their properties and values (if readable). The output is formatted for improved
human readability.

The script requires a regular expression pattern as an input argument to match the BLE device name.
If the device is not found within the number of specified attempts, the script exits.

Usage:
    python scan.py <device_name_pattern>

Arguments:
    device_name_pattern: A regular expression pattern to match against the names of BLE devices.

Example:
    python scan.py "^PL2B.*" # This will match any device name starting with 'PL2B'.

The script will attempt to find the device up to 5 times before giving up. If a device is found,
it will connect and list all available services, characteristics along with their values if they
are readable, and descriptors.

Note:
    This script is intended for educational and diagnostic purposes. It may not work with all
    BLE devices, and the interpretation of the characteristic values is left to the user.
"""

import asyncio
import re
import sys
from bleak import BleakScanner, BleakClient, BleakError

# Mapping of common characteristic UUIDs to human-readable names
CHARACTERISTIC_NAME_MAP = {
    "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer Name String",
    "00002a24-0000-1000-8000-00805f9b34fb": "Model Number String",
    "00002a25-0000-1000-8000-00805f9b34fb": "Serial Number String",
    "00002a27-0000-1000-8000-00805f9b34fb": "Hardware Revision String",
    "00002a26-0000-1000-8000-00805f9b34fb": "Firmware Revision String",
    "00002a28-0000-1000-8000-00805f9b34fb": "Software Revision String",
    "00002a23-0000-1000-8000-00805f9b34fb": "System ID",
    "00002a2a-0000-1000-8000-00805f9b34fb": "IEEE 11073-20601 Regulatory Certification Data List",
    "00002a50-0000-1000-8000-00805f9b34fb": "PnP ID",
    # Add other characteristics as needed
}

def bytearray_to_string(value):
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return value.hex()

async def list_characteristics(device_pattern, attempts=20, connection_attempts=3):
    if not device_pattern:
        print("Device name pattern must be provided.")
        return

    found_device = None
    for attempt in range(1, attempts + 1):
        devices = await BleakScanner.discover()
        for device in devices:
            if re.search(device_pattern, device.name or "", re.IGNORECASE):
                found_device = device
                break

        if found_device:
            break
        else:
            print(f"No devices found on attempt {attempt}/{attempts}. Retrying...")
            await asyncio.sleep(3)

    if not found_device:
        print(f"No devices found with pattern '{device_pattern}'.")
        return

    client = BleakClient(found_device.address)
    for attempt in range(1, connection_attempts + 1):
        try:
            if not client.is_connected:
                await client.connect()
                print(f"\nConnected to: {found_device.name} (Address: {found_device.address})\n")
                break
        except Exception as e:
            print(f"Connection attempt {attempt}/{connection_attempts} failed: {e}")
            if attempt == connection_attempts:
                print("Failed to connect to the device.")
                return
            await asyncio.sleep(1)

    try:
        for service in client.services:
            print(f"Service [{service.uuid}]\n-------------------------")
            for char in service.characteristics:
                char_name = CHARACTERISTIC_NAME_MAP.get(char.uuid, "Unknown Characteristic")
                properties = ', '.join(char.properties)
                print(f"  - Characteristic [{char.uuid}]: {char_name} (Properties: {properties})")
                if "read" in char.properties:
                    value = await client.read_gatt_char(char.uuid)
                    print(f"    -> Value: {bytearray_to_string(value)}")

                for descriptor in char.descriptors:
                    try:
                        value = await client.read_gatt_descriptor(descriptor.handle)
                        print(f"    -> Descriptor [{descriptor.uuid}]: {bytearray_to_string(value)}")
                    except Exception as e:
                        print(f"    -> Error reading descriptor [{descriptor.uuid}]: {e}")
            print("\n")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    device_pattern = None if len(sys.argv) <= 1 else sys.argv[1]
    asyncio.run(list_characteristics(device_pattern))