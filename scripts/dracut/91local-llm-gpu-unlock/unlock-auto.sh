#!/bin/sh
# Resolve only the approved three NVIDIA display models before NVIDIA binds.
local_llm_unlock() {
    case " $(cat /proc/cmdline) " in *" local_llm_gpu_unlock=auto "*) ;; *) return 0 ;; esac
    selected= perdev= n2206=0 n2208=0 n2503=0
    for dev in /sys/bus/pci/devices/*; do
        [ -r "$dev/vendor" ] && [ -r "$dev/class" ] && [ -r "$dev/device" ] || continue
        read -r vendor < "$dev/vendor"
        read -r class < "$dev/class"
        [ "$vendor" = 0x10de ] || continue
        case "$class" in 0x03*) ;; *) continue ;; esac
        read -r model < "$dev/device"
        case "$model" in
            0x2206) n2206=$((n2206+1));;
            0x2208) n2208=$((n2208+1));;
            0x2503) n2503=$((n2503+1));;
            *) continue ;;
        esac
        bdf=${dev##*/}
        selected=${selected:+$selected,}$bdf
        case "$model" in 0x2206|0x2208) perdev="${perdev}pci=$bdf;RMForceStaticBar1=0;" ;; esac
    done
    if [ "$n2206,$n2208,$n2503" != 1,1,1 ]; then
        echo 'local_llm_gpu_unlock: expected exactly one 2206, 2208, 2503; skipped' >&2
        return 1
    fi
    mkdir -p /run/modprobe.d
    printf 'options nvidia NVreg_RegistryDwordsPerDevice="%s"\n' "$perdev" > /run/modprobe.d/local-llm-dynamic-bar1.conf
    printf '%s\n' "$selected" > /run/local-llm-gpu-unlock-targets
    echo "local_llm_gpu_unlock: selected $selected" >&2
    modprobe gpu_unlock "targets=$selected"
}
local_llm_unlock || echo 'local_llm_gpu_unlock: early unlock did not complete; health verification required' >&2
