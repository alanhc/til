/* Bare-metal blink for STM32F103C8 (Blue Pill). LED on PC13, active low.
 * No HAL, no CMSIS: registers are poked directly so every line is visible in GDB.
 * Linked at 0x08002000 to run behind the dapboot bootloader.
 * Records the state dapboot hands over (VTOR, clock source) for GDB. */
#include <stdint.h>

#define RCC_APB2ENR (*(volatile uint32_t *)0x40021018)
#define GPIOC_CRH   (*(volatile uint32_t *)0x40011004)
#define GPIOC_ODR   (*(volatile uint32_t *)0x4001100C)
#define SCB_VTOR    (*(volatile uint32_t *)0xE000ED08)
#define RCC_CFGR    (*(volatile uint32_t *)0x40021004)

volatile uint32_t blink_count;   /* watch this from GDB: print blink_count */
uint32_t vtor_at_entry;          /* VTOR as dapboot left it */
uint32_t cfgr_at_entry;          /* RCC_CFGR as dapboot left it (SWS bits 3:2 = 2 means PLL) */

static void delay(uint32_t n)
{
    for (volatile uint32_t i = 0; i < n; i++) {
    }
}

int main(void)
{
    RCC_APB2ENR |= (1u << 4);              /* IOPCEN: clock GPIOC */
    GPIOC_CRH &= ~(0xFu << 20);            /* PC13 config bits [23:20] */
    GPIOC_CRH |= (0x2u << 20);             /* output push-pull, 2 MHz */

    for (;;) {
        GPIOC_ODR ^= (1u << 13);           /* toggle LED */
        blink_count++;
        delay(200000);
    }
}

/* ---- minimal startup ---- */
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;

void Reset_Handler(void)
{
    uint32_t vtor = SCB_VTOR, cfgr = RCC_CFGR;   /* read before anything changes them */
    SCB_VTOR = 0x08002000;                 /* our vectors, not dapboot's */
    uint32_t *src = &_sidata, *dst = &_sdata;
    while (dst < &_edata) *dst++ = *src++;
    for (dst = &_sbss; dst < &_ebss;) *dst++ = 0;
    vtor_at_entry = vtor;                  /* .bss is zeroed now, safe to store */
    cfgr_at_entry = cfgr;
    main();
    for (;;) {
    }
}

void Default_Handler(void)
{
    for (;;) {
    }
}

__attribute__((section(".isr_vector"), used))
void (*const vectors[])(void) = {
    (void (*)(void))&_estack,   /* initial SP */
    Reset_Handler,
    Default_Handler,            /* NMI */
    Default_Handler,            /* HardFault */
    Default_Handler,            /* MemManage */
    Default_Handler,            /* BusFault */
    Default_Handler,            /* UsageFault */
};
