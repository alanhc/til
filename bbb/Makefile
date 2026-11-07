# Out-of-tree build against the BBB kernel tree:
#   make            build usr_led.ko and the dtb
#   make clean
obj-m := usr_led.o

KSRC ?= $(HOME)/bbb-bringup/linux
KOBJ ?= $(HOME)/bbb-bringup/build-arm
MAKEARGS := ARCH=arm CROSS_COMPILE=arm-linux-gnueabihf-
DTS_INC := -I $(KSRC)/arch/arm/boot/dts/ti/omap -I $(KSRC)/include

all: modules dtb

modules:
	$(MAKE) $(MAKEARGS) -C $(KSRC) O=$(KOBJ) M=$(CURDIR) modules

# The dts is outside the kernel tree, so preprocess and compile it by hand the
# way the kernel's dtb rule does.
dtb: am335x-boneblack-usrled.dtb
am335x-boneblack-usrled.dtb: am335x-boneblack-usrled.dts
	cpp -nostdinc $(DTS_INC) -undef -D__DTS__ -x assembler-with-cpp $< -o $@.tmp
	$(KOBJ)/scripts/dtc/dtc -I dts -O dtb -i $(KSRC)/arch/arm/boot/dts/ti/omap -o $@ $@.tmp
	rm -f $@.tmp

clean:
	$(MAKE) $(MAKEARGS) -C $(KSRC) O=$(KOBJ) M=$(CURDIR) clean
	rm -f am335x-boneblack-usrled.dtb
