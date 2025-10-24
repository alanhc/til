---
title: porting pmbus driver
---
# porting pmbus driver guide
## Overview
We need to implement a PMBus sensor driver so that it can be accessed from userspace applications.
The key tasks when porting the driver are to define the `probe()` function and determine how PMBus commands will be sent to the sensor.
![image](https://hackmd.io/_uploads/rkRRRj3Blx.png)


## Read Schematic
- Device is on `i2c8` (counting starts from 1 in schematic)

## Scan Devices
- **Make sure the device address matches the schematic.**  
  If not, determine whether the issue lies in the schematic or identify the incorrect device.

![image](https://hackmd.io/_uploads/HkoDvihBgx.png)



## Write the Device Tree

- **Path**:  
  `<linux>/arch/arm/boot/dts/aspeed-<project>-ast2600-<board>-swb-i2c.dtsi`

### Device Tree Structure
Find the correct location to insert your device node:

```
- aspeed-<project>-<board>-evt.dts
    - aspeed-<project>-ast2600-<board>.dtsi
        - aspeed-<project>-ast2600-<board>-swb.dtsi
            - aspeed-<project>-ast2600-<board>-swb-i2c.dtsi
```
```dts
&i2c7 {
	status = "okay";
	...
	mpc42013@63 {
		compatible = "mps,mpc42013";
		reg = <0x63>;
	};
```
## Kconfig
- `/home/alan/<linux>/drivers/hwmon/pmbus/Kconfig`
Define a config option so the kernel can recognize and enable the driver through menuconfig.

```
config SENSORS_MPC42013
	tristate "MPS MPC42013"
	help
	  If you say yes here you get hardware monitoring support for MPS
	  MPC42013.

	  This driver can also be built as a module. If so, the module will
	  be called mpc42013.
```

## Default configuration file
- `y`: built into kernel
- `m`: compiled as a module
**Path**:
`<linux>/arch/arm/configs/aspeed_<project>_defconfig`


## Makefile
**Path**: 
`<linux>/drivers/hwmon/pmbus/Makefile
`
Tell the compiler to build this driver if .config has CONFIG_SENSORS_MPC42013=y or =m.

```makefile
obj-$(CONFIG_SENSORS_MPC42013)	+= mpc42013.o
```



## driver code
- **path**:
`<linux>/drivers/hwmon/pmbus/mpc42013.c`

### Code Structure
- [pmbus driver template](https://gist.github.com/alanhc/3bcc48d62040e4063fdf887ac669208a)

![image](https://hackmd.io/_uploads/HyFJ1nhSll.png)

### device table
```
MODULE_DEVICE_TABLE(i2c, mpc42013_id);
```
### driver structure
```c
static struct i2c_driver mpc42013_driver = {
    .driver = {
        .name = "mpc42013",
        .of_match_table = of_match_ptr(mpc42013_of_match),
    },
    .probe_new = mpc42013_probe,
    .remove = pmbus_do_remove,
    .id_table = mpc42013_id,
};
module_i2c_driver(mpc42013_driver);
```
### Read datasheet
![image](https://hackmd.io/_uploads/Sy5qXhhree.png)
### `.probe`
- Flow
    1. finish `pmbus_driver_info` struct
    2. `pmbus_do_probe(client, info)`

#### driver info structure `pmbus_driver_info`
- `.pages`: Specifies the number of pages supported by the device.
- `.format[PSC_VOLTAGE_IN] = direct`: Defines the PMBus data format for input voltage; the format types are defined in `pmbus.h`.
    - pmbus data format
        - linear (m=1)
        - direct
            - Fill in the $m$, $b$, and $R$ values according to the following formula:
                $$
                X = \frac{1}{m} \cdot \left( Y \cdot 10^{-R} - b \right)
                $$
            - code: 
                ```c
                info = devm_kmemdup(dev, &mpc42013_info, sizeof(*info), GFP_KERNEL);
                ...
                info->m[PSC_VOLTAGE_IN] = 8;
                info->b[PSC_VOLTAGE_IN] = 0;
                info->R[PSC_VOLTAGE_IN] = 0;
- `.func[0]`: Enables supported PMBus commands using the functionality bitmask, also defined in `pmbus.h`.



### `.read_word_data`  
- `.read_word_data = mpc42013_read_word_data`:
Assigns the driver's word data read handler. This function is responsible for reading sensor values.

- Inside the function:
`int raw = pmbus_read_word_data(client, page, phase, reg);`
This API sends a PMBus command to the device to read a 16-bit word from the specified register.

PMBus register constants, such as PMBUS_READ_VIN, are defined in pmbus.h.




## Driver Doumentation
- `<linux>/Documentation/devicetree/bindings/hwmon/pmbus/mps,mpc42013,yaml`

```
# SPDX-License-Identifier: (GPL-2.0 OR BSD-2-Clause)
%YAML 1.2
---

$id: http://devicetree.org/schemas/hwmon/pmbus/mps,mpc42013,yaml
$schema: http://devicetree.org/meta-schemas/core.yaml#

title: MPS MPC 42013

maintainers:
  -Alan Tseng <alan_tseng@example.com>

description: |
  MPC 42013 pmbus driver
 
properties:
  compatible:
    enum:
      - mps, mpc42013

  reg:
    maxItems: 1
```
## Verify
- Verify that the input and output values satisfy the following equation and fall within the value ranges specified in the schematic.
$$P=I*V$$

## Useful cmd
```
i2cget -fy 7 0x63 0x8c w 
```

Find driver in which hwmon:
```
for d in /sys/class/hwmon/hwmon*; do
  echo -n "$d → "
  cat "$d/name"
done
```

```shell
for f in /sys/class/hwmon/hwmon19/*_label; do
  printf "%-10s : %s\n" "${f##*/%_label}" "$(cat "$f")"
done
```
![image](https://hackmd.io/_uploads/BylZZrCSgl.png)

## Make Flash
**Path**: `buildroot/`
```
export IMAGE="<project>-fw-<board>-1.1.x.x.img"

dd if=./output/build/uboot-custom/u-boot.bin of=$IMAGE conv=notrunc bs=1 seek=65536

dd if=./output/build/linux-custom/arch/arm/boot/uImage of=$IMAGE conv=notrunc bs=1 seek=524288

dd if=./output/build/linux-custom/arch/arm/boot/dts/aspeed-<project>-<board>-evt.dtb of=$IMAGE conv=notrunc bs=1 seek=12689408
```

## Upload
```
scp $IMAGE root@$BMC_IP:/var/
ssh root@$BMC_IP

dd if=/var/<project>-fw-<board>-1.1.x.x.img of=/dev/mtdblock0 bs=64k seek=0
reboot
```


## Table

| name | function bit mask | reg | sys |
| -------- | -------- | -------- | -------- | 
|   VIN   | PMBUS_HAVE_VIN     | PMBUS_READ_VIN     | in1
| VOUT     | PMBUS_HAVE_VOUT     | PMBUS_READ_VOUT     | in2
| POUT     | PMBUS_HAVE_POUT     | PMBUS_READ_POUT     | power2
| IOUT     | PMBUS_HAVE_IOUT     | PMBUS_READ_IOUT     | curr2

## Materials

- https://pmbus.org/wp-content/uploads/2017/07/2017_APEC_PMBus_Direct_Data_Xfer_Format.pdf
- https://docs.kernel.org/hwmon/pmbus.html
