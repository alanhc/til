# Build blink.elf with the Arm GNU Toolchain (arm-none-eabi-gcc must be on PATH,
# or set $env:ARM_TC to the toolchain's bin directory).
$tc = if ($env:ARM_TC) { "$env:ARM_TC\" } else { '' }
Set-Location $PSScriptRoot
& "${tc}arm-none-eabi-gcc" -mcpu=cortex-m3 -mthumb -O0 -g3 -ffreestanding -nostdlib `
    -Wall -T stm32f103c8.ld '-Wl,-Map=blink.map' -o blink.elf blink.c
if ($LASTEXITCODE -eq 0) { & "${tc}arm-none-eabi-size" blink.elf }
