// SPDX-License-Identifier: GPL-2.0
/*
 * Minimal platform driver for BeagleBone Black bring-up practice, using the
 * LED class.
 *
 * Binds to a device tree node like
 *
 *	usr-led {
 *		compatible = "bringup,usr-led";
 *		led-gpios = <&gpio1 24 GPIO_ACTIVE_HIGH>;
 *		label = "bringup:green:usr3";	(optional)
 *	};
 *
 * and registers it with the LED class, so it shows up under /sys/class/leds/
 * with brightness and trigger files like any other LED.
 *
 * The first version of this driver had its own "on" sysfs attribute; that is
 * kept in usr_led_sysfs.c.orig for comparison.
 */

#include <linux/gpio/consumer.h>
#include <linux/leds.h>
#include <linux/mod_devicetable.h>
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/property.h>

struct usr_led {
	struct led_classdev cdev;
	struct gpio_desc *gpio;
};

/*
 * The LED core only hands us the led_classdev. It is embedded in struct
 * usr_led, so step back from it to the containing structure.
 */
static inline struct usr_led *cdev_to_usr_led(struct led_classdev *cdev)
{
	return container_of(cdev, struct usr_led, cdev);
}

/*
 * Triggers such as heartbeat call this from timer context, where sleeping is
 * not allowed. That is fine for a GPIO in the SoC, which is a register write.
 */
static void usr_led_set(struct led_classdev *cdev, enum led_brightness value)
{
	gpiod_set_value(cdev_to_usr_led(cdev)->gpio, value != LED_OFF);
}

/*
 * A GPIO behind an I2C or SPI expander needs a bus transfer, which can sleep.
 * The LED core runs this one from a workqueue instead.
 */
static int usr_led_set_blocking(struct led_classdev *cdev,
				enum led_brightness value)
{
	gpiod_set_value_cansleep(cdev_to_usr_led(cdev)->gpio, value != LED_OFF);
	return 0;
}

static int usr_led_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct usr_led *led;
	int ret;

	led = devm_kzalloc(dev, sizeof(*led), GFP_KERNEL);
	if (!led)
		return -ENOMEM;

	led->gpio = devm_gpiod_get(dev, "led", GPIOD_OUT_LOW);
	if (IS_ERR(led->gpio))
		return dev_err_probe(dev, PTR_ERR(led->gpio),
				     "failed to get led GPIO\n");

	led->cdev.name = "bringup:green:usr3";
	device_property_read_string(dev, "label", &led->cdev.name);
	led->cdev.max_brightness = 1;
	if (gpiod_cansleep(led->gpio))
		led->cdev.brightness_set_blocking = usr_led_set_blocking;
	else
		led->cdev.brightness_set = usr_led_set;

	/*
	 * Unregistering switches the LED off unless LED_RETAIN_AT_SHUTDOWN is
	 * set, and devm unregisters it before the GPIO is released, so there
	 * is no remove callback left to write.
	 */
	ret = devm_led_classdev_register(dev, &led->cdev);
	if (ret)
		return dev_err_probe(dev, ret, "failed to register LED\n");

	dev_info(dev, "registered as %s\n", led->cdev.name);
	return 0;
}

static const struct of_device_id usr_led_of_match[] = {
	{ .compatible = "bringup,usr-led" },
	{ }
};
MODULE_DEVICE_TABLE(of, usr_led_of_match);

static struct platform_driver usr_led_driver = {
	.probe = usr_led_probe,
	.driver = {
		.name = "usr-led",
		.of_match_table = usr_led_of_match,
	},
};
module_platform_driver(usr_led_driver);

MODULE_DESCRIPTION("BeagleBone Black USR LED practice driver (LED class)");
MODULE_LICENSE("GPL");
