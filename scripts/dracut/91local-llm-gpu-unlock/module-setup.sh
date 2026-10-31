#!/bin/bash
check() { return 0; }
depends() { echo kernel-modules; return 0; }
installkernel() { instmods gpu_unlock; }
install() {
    inst_multiple modprobe cat mkdir
    inst_hook pre-udev 00 "$moddir/unlock-auto.sh"
}
