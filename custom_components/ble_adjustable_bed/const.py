DOMAIN = "ble_adjustable_bed"

DEVICE_NAME = "Adjustable Bed"
MANUFACTURER = "Galaxy"
MODEL = "26W-N"

# BLE UUIDs
BED_SERVICE_UUID = "0000fee9-0000-1000-8000-00805f9b34fb"
BED_CHAR_UUID = "d44bc439-abfd-45a2-b575-925416129600"

# Simulated movement
COVER_MOVE_STEP = 1          # % per actie
COVER_MOVE_DELAY = 0.15      # seconden

HEAD_UP_CMD = "head_up"
HEAD_DOWN_CMD = "head_down"
FEET_UP_CMD = "feet_up"
FEET_DOWN_CMD = "feet_down"

# Bed commands (5 bytes each)
BED_COMMANDS = {
    "light": bytearray([0x6E, 0x01, 0x00, 0x3C, 0xAB]),
    "zero_gravity": bytearray([0x6E, 0x01, 0x00, 0x45, 0xB4]),
    "flat": bytearray([0x6E, 0x01, 0x00, 0x31, 0xA0]),
    "head_up": bytearray([0x6E, 0x01, 0x00, 0x24, 0x93]),
    "head_down": bytearray([0x6E, 0x01, 0x00, 0x25, 0x94]),
    "feet_up": bytearray([0x6E, 0x01, 0x00, 0x26, 0x95]),
    "feet_down": bytearray([0x6E, 0x01, 0x00, 0x27, 0x96]),
}
