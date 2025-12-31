DOMAIN = "ble_adjustable_bed"

DEVICE_NAME = "Adjustable-Bed Ble"
MANUFACTURER = "Galaxy"
MODEL = "26W-N"

# BLE UUIDs (afkomstig uit ESPHome)
SERVICE_UUID = "0000fee9-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "d44bc439-abfd-45a2-b575-925416129600"

# Power commands zg and flad
POWER_ON_COMMAND = bytearray([0x6e, 0x01, 0x00, 0x45, 0xb4])
POWER_OFF_COMMAND = bytearray([0x6e, 0x01, 0x00, 0x31, 0xa0])
