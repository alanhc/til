#!/bin/bash
# Send one command to the board and print its output (until the next "=> ").
# usage: ub.sh 'bdinfo'
L=${BBB_DIR:-$HOME/bbb-bringup}/logs/current.log
F=${BBB_DIR:-$HOME/bbb-bringup}/logs/tx.fifo
n=$(wc -l < "$L")
printf '%s\r' "$1" > "$F"
for i in $(seq 1 ${2:-50}); do
  sleep 0.2
  tail -n +$((n+1)) "$L" | grep -q '\] => *$' && break
done
tail -n +$((n+1)) "$L" | sed 's/^\[[0-9:]*\] //'
