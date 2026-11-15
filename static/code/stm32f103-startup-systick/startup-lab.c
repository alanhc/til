/* startup-lab: the smallest STM32F103 program that still has a real startup.
 * No HAL, no CMSIS, no libc. Lives at 0x08002000, behind dapboot. */
#include <stdint.h>

/* ---------- 1. registers we touch (addresses from RM0008) ---------- */
#define RCC_APB2ENR (*(volatile uint32_t *)0x40021018)
#define GPIOC_CRH   (*(volatile uint32_t *)0x40011004)
#define GPIOC_ODR   (*(volatile uint32_t *)0x4001100C)
#define SCB_VTOR    (*(volatile uint32_t *)0xE000ED08)

/* ---------- 2. two globals, one per RAM section ---------- */
uint32_t speed = 200000;        /* has a value  -> .data (copied from flash) */
uint32_t blink_count;           /* no value     -> .bss  (must be zeroed)    */

/* ---------- 3. the program ---------- */
int main(void)
{
    RCC_APB2ENR |= (1u << 4);           /* turn on GPIOC's clock          */
    GPIOC_CRH = (GPIOC_CRH & ~(0xFu << 20)) | (0x2u << 20); /* PC13 = output */

    for (;;) {
        GPIOC_ODR ^= (1u << 13);        /* flip the LED                   */
        blink_count++;
        for (volatile uint32_t i = 0; i < speed; i++) {
        }
    }
}

/* ---------- 4. the startup: what runs BEFORE main ---------- */
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss, _estack;  /* from the .ld */

void Reset_Handler(void)
{
    SCB_VTOR = 0x08002000;              /* our vector table, not dapboot's */

    uint32_t *src = &_sidata;           /* .data: copy initial values      */
    uint32_t *dst = &_sdata;            /*        from flash into RAM      */
    while (dst < &_edata)
        *dst++ = *src++;

    for (dst = &_sbss; dst < &_ebss; )  /* .bss: fill with zero            */
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

/* ---------- 5. the vector table: the first thing the CPU reads ---------- */
__attribute__((section(".isr_vector"), used))
void (*const vectors[])(void) = {
    (void (*)(void))&_estack,   /* [0] initial SP  */
    Reset_Handler,              /* [1] reset       */
    Default_Handler,            /* [2] NMI         */
    Default_Handler,            /* [3] HardFault   */
};
