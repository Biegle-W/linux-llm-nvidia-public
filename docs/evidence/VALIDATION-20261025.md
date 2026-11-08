# Preparation validation — October 25, 2026

Eleven host-only unit tests pass, including explicit current-address selection of
the Ti/3080 pair and Ti/3080/3060 trio, rejection of unknown/duplicate targets,
Windows/WSL and Secure Boot guards, GRUB argument preservation, shell syntax and
boot-image rollback. Driver, GPU and initramfs operations are mocked. Windows Git
Bash needed normal host access for its named objects; no test was skipped to hide
that sandbox restriction. Native Linux installation/unlock/performance remain
untested. The reviewed upstream pin is unchanged; its device table includes 2206.
