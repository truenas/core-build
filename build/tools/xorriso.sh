#!/bin/sh
# Yes, Yes, this is nasty...
# Done to work-around xorriso seg-fault when assembling ISOs with BIOS + EFI
# We don't care about HFS that much..

ARGS=`echo $@ | sed 's|-hfsplus -apm-block-size 2048 -hfsplus-file-creator-type chrp tbxj /System/Library/CoreServices/.disk_label -hfs-bless-by i /System/Library/CoreServices/boot.efi||g'`
xorriso $ARGS
