# Run the STM32F103 ROM bootloader under GDB, step by step, without touching BOOT0.
# Start OpenOCD first:
#   openocd -f ft232h-jtag.cfg -f target/stm32f1x.cfg
# then:
#   arm-none-eabi-gdb -q -batch -x run-rom.gdb
# Addresses are from one STM32F103C8T6; check them against your own disassembly.
set pagination off
set confirm off
target extended-remote localhost:3333
monitor reset halt

echo \n== 1. pretend BOOT0=1: load MSP and PC from the ROM vector table\n
x/4xw 0x1FFFF000
set $xpsr = 0x01000000
set $msp = *(unsigned*)0x1FFFF000
set $pc  = *(unsigned*)0x1FFFF004 & ~1
printf "msp=0x%08x pc=0x%08x\n", $msp, $pc

echo \n== 2. Reset_Handler and __main, one instruction at a time\n
set $i = 0
while $i < 4
  x/i $pc
  stepi
  printf "   -> pc=0x%08x r0=0x%08x sp=0x%08x\n", $pc, $r0, $sp
  set $i = $i + 1
end

echo \n== 3. __scatterload: region table start and end\n
x/4i $pc
stepi
stepi
printf "r4(table start)=0x%08x r5(table end)=0x%08x\n", $r4, $r5
hbreak *0x1FFFF34C
continue

echo \n== 4. into C main\n
printf "pc=0x%08x lr=0x%08x sp=0x%08x\n", $pc, $lr, $sp
delete

echo \n== 5. main, stage by stage\n
printf "before: RCC_CR=0x%08x RCC_CFGR=0x%08x APB2ENR=0x%08x GPIOA_CRH=0x%08x\n", *(unsigned*)0x40021000, *(unsigned*)0x40021004, *(unsigned*)0x40021018, *(unsigned*)0x40010804
hbreak *0x1FFFF35E
continue
printf "[stack copy] sp=0x%08x, GET reply on stack:\n", $sp
x/16xb $sp+4
printf "PRIMASK=%d\n", $primask
delete
hbreak *0x1FFFF384
continue
printf "[PLL]  RCC_CR=0x%08x RCC_CFGR=0x%08x\n", *(unsigned*)0x40021000, *(unsigned*)0x40021004
delete
hbreak *0x1FFFF390
continue
printf "[SW]   RCC_CFGR=0x%08x APB2ENR=0x%08x\n", *(unsigned*)0x40021004, *(unsigned*)0x40021018
delete
hbreak *0x1FFFF3AA
continue
printf "[IO]   VTOR=0x%08x GPIOA_CRH=0x%08x SysTick CTRL=0x%x LOAD=0x%x\n", *(unsigned*)0xE000ED08, *(unsigned*)0x40010804, *(unsigned*)0xE000E010, *(unsigned*)0xE000E014
delete

echo \n== 6. autobaud loop: polling PA10\n
set $i = 0
while $i < 6
  x/i $pc
  stepi
  set $i = $i + 1
end
printf "GPIOA_IDR=0x%04x PA10=%d\n", *(unsigned*)0x40010808, (*(unsigned*)0x40010808 >> 10) & 1

echo \n== 7. pretend we measured 115200 baud: r5 = 24MHz / 115200 * 7\n
set $pc = 0x1FFFF3D6
set $r5 = 1458
set $r1 = 0
hbreak *0x1FFFF3F2
continue
printf "[USART1] BRR=0x%04x (%d) CR1=0x%04x\n", *(unsigned*)0x40013808, *(unsigned*)0x40013808, *(unsigned*)0x4001380C
delete
hbreak *0x1FFFF3F8
continue
printf "[ACK]  0x79 sent, USART1_SR=0x%04x\n", *(unsigned*)0x40013800
delete
x/6i $pc

monitor reset run
detach
quit
