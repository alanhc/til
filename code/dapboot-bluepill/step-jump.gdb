set pagination off
set confirm off
target extended-remote localhost:3333
monitor reset halt
hbreak *0x080013c2
continue
printf "\n== at jump sequence: pc=0x%08x msp=0x%08x VTOR=0x%08x\n", $pc, $msp, *(unsigned*)0xE000ED08
printf "   app vector [0]=0x%08x [1]=0x%08x\n", *(unsigned*)0x08002000, *(unsigned*)0x08002004
set $i = 0
while $i < 8
  x/i $pc
  stepi
  printf "   -> pc=0x%08x r2=0x%08x r3=0x%08x msp=0x%08x VTOR=0x%08x\n", $pc, $r2, $r3, $msp, *(unsigned*)0xE000ED08
  set $i = $i + 1
end
add-symbol-file app.elf
printf "\n== now in app: "
info symbol $pc
delete
monitor resume
detach
quit
