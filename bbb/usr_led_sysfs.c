// SPDX-License-Identifier: GPL-2.0
/*
 * Minimal platform driver for BeagleBone Black bring-up practice.
 *
 * Binds to a device tree node like
 *
 *	usr-led {
 *		compatible = "bringup,usr-led";
 *		led-gpios = <&gpio1 24 GPIO_ACTIVE_HIGH>;
 *	};
 *
 * and exposes /sys/bus/platform/devices/usr-led/on: write 1 or 0 to switch
 * the LED, read it back to see the current state.
 */

#include <linux/gpio/consumer.h>
#include <linux/mod_devicetable.h>
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/sysfs.h>

struct usr_led {
	struct gpio_desc *gpio;
	bool on;
};

static ssize_t on_show(struct device *dev, struct device_attribute *attr,
		       char *buf)
{
	struct usr_led *led = dev_get_drvdata(dev);

	return sysfs_emit(buf, "%d\n", led->on);
}

static ssize_t on_store(struct device *dev, struct device_attribute *attr,
			const char *buf, size_t count)
{
	struct usr_led *led = dev_get_drvdata(dev);
	bool on;
	int ret;

	ret = kstrtobool(buf, &on);
	if (ret)
		return ret;

	gpiod_set_value(led->gpio, on);
	led->on = on;
	return count;
}
static DEVICE_ATTR_RW(on);

static struct attribute *usr_led_attrs[] = {
	&dev_attr_on.attr,
	NULL
};
ATTRIBUTE_GROUPS(usr_led);

static int usr_led_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct usr_led *led;

	led = devm_kzalloc(dev, sizeof(*led), GFP_KERNEL);
	if (!led)
		return -ENOMEM;

	/*
	 * Looks up the "led-gpios" property, requests the GPIO and makes it an
	 * output driven high: the OE and SETDATAOUT writes done by hand in
	 * U-Boot, through gpiolib and gpio-omap.
	 */
	led->gpio = devm_gpiod_get(dev, "led", GPIOD_OUT_HIGH);
	if (IS_ERR(led->gpio))
		return dev_err_probe(dev, PTR_ERR(led->gpio),
				     "failed to get led GPIO\n");
	led->on = true;

	platform_set_drvdata(pdev, led);
	dev_info(dev, "probed, LED on\n");
	return 0;
}

static void usr_led_remove(struct platform_device *pdev)
{
	struct usr_led *led = platform_get_drvdata(pdev);

	gpiod_set_value(led->gpio, 0);
	dev_info(&pdev->dev, "removed, LED off\n");
}

static const struct of_device_id usr_led_of_match[] = {
	{ .compatible = "bringup,usr-led" },
	{ }
};
MODULE_DEVICE_TABLE(of, usr_led_of_match);

static struct platform_driver usr_led_driver = {
	.probe = usr_led_probe,
	.remove = usr_led_remove,
	.driver = {
		.name = "usr-led",
		.of_match_table = usr_led_of_match,
		.dev_groups = usr_led_groups,
	},
};
module_platform_driver(usr_led_driver);

MODULE_DESCRIPTION("BeagleBone Black USR LED practice driver");
MODULE_LICENSE("GPL");
