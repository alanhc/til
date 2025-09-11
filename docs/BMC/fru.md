
/sys/bus/i2c/devices/13-0048

/sys/bus/i2c/devices/13-0048/# hexdump -C eeprom

i2ctransfer -y -f 13 w2@0x48 0x00 0x00 r128