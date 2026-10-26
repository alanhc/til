#!/bin/bash
# Run a command on the BBB over SSH with a password (no key set up yet).
# Set BBB_PASS in the environment; nothing is stored in this file.
: "${BBB_PASS:?set BBB_PASS to the BBB debian password (export it)}"
A=$(mktemp); trap 'rm -f $A' EXIT
printf '#!/bin/sh\necho "$BBB_PASS"\n' > $A; chmod 700 $A
SSH_ASKPASS=$A SSH_ASKPASS_REQUIRE=force DISPLAY=:0 timeout ${T:-20} \
  ssh -o PubkeyAuthentication=no -o LogLevel=ERROR -o ConnectTimeout=5 debian@${BBB_IP:-192.168.10.242} "$@" < /dev/null 2>&1 \
  | grep -vE '^(Debian GNU|BeagleBoard.org|Support:|default username)|^$'
