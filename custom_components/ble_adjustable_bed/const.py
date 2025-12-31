DOMAIN = "ble_adjustable_bed"

DEVICE_NAME = "BK-Light iPixel"
MANUFACTURER = "BK-Light"
MODEL = "iPixel 32x32"

# BLE UUIDs (afkomstig uit ESPHome)
SERVICE_UUID = "000000fa-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000fa02-0000-1000-8000-00805f9b34fb"

# Power commands
POWER_ON_COMMAND = bytearray([0x05, 0x00, 0x07, 0x01, 0x01])
POWER_OFF_COMMAND = bytearray([0x05, 0x00, 0x07, 0x01, 0x00])
