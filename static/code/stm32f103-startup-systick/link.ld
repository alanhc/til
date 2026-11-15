/* Where things go. dapboot owns the first 8KB of flash. */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08002000, LENGTH = 56K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 20K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);    /* stack starts at the top of RAM */
ENTRY(Reset_Handler)

SECTIONS
{
    .isr_vector : { KEEP(*(.isr_vector)) } > FLASH   /* must be first */
    .text       : { *(.text*) *(.rodata*) } > FLASH

    _sidata = LOADADDR(.data);                      /* where .data sits in flash */
    .data : { _sdata = .; *(.data*) _edata = .; } > RAM AT > FLASH
    .bss  : { _sbss = .; *(.bss*) *(COMMON) _ebss = .; } > RAM
}
