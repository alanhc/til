/* systick-lab: blink driven by the SysTick interrupt instead of a busy loop.
 * Same startup as startup-lab; the vector table grows to 16 entries. */
#include <stdint.h>

#define RCC_APB2ENR (*(volatile uint32_t *)0x40021018)
#define GPIOC_CRH   (*(volatile uint32_t *)0x40011004)
#define GPIOC_ODR   (*(volatile uint32_t *)0x4001100C)
#define SCB_VTOR    (*(volatile uint32_t *)0xE000ED08)
#define SYST_CSR    (*(volatile uint32_t *)0xE000E010)   /* SysTick control   */
#define SYST_RVR    (*(volatile uint32_t *)0xE000E014)   /* SysTick reload    */
#define SYST_CVR    (*(volatile uint32_t *)0xE000E018)   /* SysTick current   */

uint32_t half_period_ms = 500;  /* .data: LED toggles every 500 ms          */
volatile uint32_t ms;           /* .bss : counted up by the interrupt       */

/* Runs by itself every 1 ms. Nobody calls it: the CPU jumps here. */
void SysTick_Handler(void)
{
    ms++;
    if (ms % half_period_ms == 0)
        GPIOC_ODR ^= (1u << 13);
}

int main(void)
{
    RCC_APB2ENR |= (1u << 4);
    GPIOC_CRH = (GPIOC_CRH & ~(0xFu << 20)) | (0x2u << 20);

    /* After a bare reset the CPU runs on HSI 8 MHz, but we are started by
     * dapboot, which already switched to HSE 8 MHz x 9 = 72 MHz for USB
     * (measured: RCC_CFGR = 0x001DC40A). So 72000 ticks = 1 ms. */
    SYST_RVR = 72000 - 1;       /* counts 71999 .. 0, so 72000 ticks        */
    SYST_CVR = 0;               /* start from a clean count                 */
    SYST_CSR = 0x7;             /* bit2 CPU clock, bit1 interrupt, bit0 on  */

    for (;;)
        __asm volatile ("wfi"); /* sleep until the next interrupt           */
}

/* ---------- startup (same as startup-lab) ---------- */
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;

void Reset_Handler(void)
{
#ifndef VTOR_VALUE
#define VTOR_VALUE 0x08002000
#endif
#ifndef NO_VTOR
    SCB_VTOR = VTOR_VALUE;      /* where the CPU looks up interrupt handlers */
#endif
    uint32_t *src = &_sidata, *dst = &_sdata;
    while (dst < &_edata)
        *dst++ = *src++;
    for (dst = &_sbss; dst < &_ebss; )
        *dst++ = 0;
    main();
    for (;;) {
    }
}

void Default_Handler(void)
{
    for (;;) {
    }
}

/* Cortex-M fixes the first 16 slots. SysTick is slot 15 (offset 0x3C). */
__attribute__((section(".isr_vector"), used))
void (*const vectors[16])(void) = {
    [0]  = (void (*)(void))&_estack,
    [1]  = Reset_Handler,
    [2]  = Default_Handler,     /* NMI        */
    [3]  = Default_Handler,     /* HardFault  */
    [4]  = Default_Handler,     /* MemManage  */
    [5]  = Default_Handler,     /* BusFault   */
    [6]  = Default_Handler,     /* UsageFault */
                                /* 7-10 reserved, left 0 */
    [11] = Default_Handler,     /* SVCall     */
    [12] = Default_Handler,     /* DebugMon   */
                                /* 13 reserved */
    [14] = Default_Handler,     /* PendSV     */
    [15] = SysTick_Handler,     /* SysTick    */
};
