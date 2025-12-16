# Device Driver

probe

kconfig

makefile

dmesg

/sys/class/hwmon/hwmonX/current1_input

改 driver 通常會動到的是 Driver 及 Device Tree
```mermaid
graph TD
    A[Buildroot]
    B[linux kernel]
    C[uboot]
    D[Driver]
    E[Device tree]

    A --> B
    A --> C
    B --> D
    B --> E

    style D stroke:red,stroke-width:2px
    style E stroke:red,stroke-width:2px
```

## smbus
![alt text](../../image-4.png)
![alt text](../../image-5.png)

## pmbus

### Linear11 Floating-Point Format
![alt text](../../image-1.png)

$$
\text{Value Represented} = Y \times 2^N
$$


```
user space（例如：sensors） 
   ↓
PMBus core
   ↓
mpc42013_read_word_data(client, page, reg)
   ↓
底層實際透過 I2C 傳送 command code（reg） → 取得 word 資料
```

可以用 `i2cdetect` 查看是否有 driver 佔用

![alt text](../../image.png)

上圖代表在 i2c-7 有 address `0x63` 的裝置， `63` 代表 no device driver，`UU` 代表目前有 driver 佔用。

### Files
- Kconfig
   `linux/drivers/hwmon/pmbus/Kconfig`
```
config {driver}
   ...
```

:::info 參考
- https://docs.kernel.org/kbuild/kconfig-language.html
- https://www.cnblogs.com/chorm590/p/13977818.html
:::

- Driver Documentation
   - 位置: `linux/Documentation/devicetree/bindings/hwmon/{driver}.yaml`
- Makefile
   - 位置: `linux/drivers/hwmon/pmbus/Makefile`

   ```makefile
   obj-$(CONFIG_{driver}) += {driver}.o
   ```

- Driver Code
   - 位置: `linux/drivers/hwmon/pmbus/{driver}.c`
- Device Tree Alias
   - 位置: `linux/arch/arm/boot/dts/{board}-i2c-aliases.dtsi`
      ```
      alias {
         i2c99 = &{sensor}
      }
      ```
### Driver Structure
![alt text](../../image-3.png)
### Functions
- `probe`
![alt text](../../image-2.png)

```c
int pmbus_read_word_data(struct i2c_client *client, u8 page, u8 phase, u8 reg);
int pmbus_read_byte_data(struct i2c_client *client, int page, u8 reg);
int pmbus_write_word_data(struct i2c_client *client, u8 page, u8 reg, u16 word);
```
- https://www.kernel.org/doc/html/v6.12/hwmon/pmbus-core.html


### 觀察
- `ls /sys/class/hwmon/hwmon16`
![alt text](../../image-6.png)

## Ref
- https://en.wikipedia.org/wiki/Power_Management_Bus
- https://www.ti.com/download/trng/docs/seminar/Topic_6_Hesse.pdf
