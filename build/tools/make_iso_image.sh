#!/bin/sh
#
# Module: mkisoimages.sh
# Author: Jordan K Hubbard
# Date:   22 June 2001
#
# $FreeBSD$
#
# This script is used by release/Makefile to build the (optional) ISO images
# for a FreeBSD release.  It is considered architecture dependent since each
# platform has a slightly unique way of making bootable CDs.  This script
# is also allowed to generate any number of images since that is more of
# publishing decision than anything else.
#
# Usage:
#
# mkisoimages.sh image-label image-name obj-dir root-dir
#
# image-label is the ISO image label
# image-name is the filename of the resulting ISO image
# obj-dir is the built object tree
# root-dir contains the image contents

if [ $# -lt 4 ]; then
	echo "Usage: $0 image-label image-name obj-dir root-dir"
	exit 1
fi

LABEL="$1"
NAME="$2"
OBJDIR="$3"
ROOTDIR="$4"
shift 4

if [ -z $ETDUMP ]; then
	ETDUMP=$OBJDIR/usr/bin/etdump
fi

if [ -z $MAKEFS ]; then
	MAKEFS=$OBJDIR/usr/sbin/makefs
fi

if [ -z $MKIMG ]; then
	MKIMG=$OBJDIR/usr/bin/mkimg
fi

stagedir=$(mktemp -d /tmp/stand-temp.XXXXXX)
mkdir -p "$stagedir/efi/boot"
cp "$OBJDIR/boot/loader.efi" "$stagedir/efi/boot/bootx64.efi"
$MAKEFS -t msdos \
    -o fat_type=12 \
    -o media_descriptor=248 \
    -o sectors_per_cluster=1 \
    -s 800k \
    efiboot.img "$stagedir"
rm -rf "$stagedir"

$MAKEFS -t cd9660 \
    -o bootimage="i386;$OBJDIR/boot/cdboot" -o no-emul-boot \
    -o bootimage="i386;efiboot.img" -o no-emul-boot -o platformid="efi" \
    -o rockridge \
    -o label="$LABEL" \
    -o publisher="iXsystems Inc.  https://www.ixsystems.com/" \
    "$NAME" "$ROOTDIR"
rm -f efiboot.img

# Look for the EFI System Partition image we dropped in the ISO image.
for entry in `$ETDUMP --format shell $NAME`; do
	eval $entry
	if [ "$et_platform" = "efi" ]; then
		espstart=`expr $et_lba \* 2048`
		espsize=`expr $et_sectors \* 512`
		espparam="-p efi::$espsize:$espstart"
		break
	fi
done

# Create a GPT image containing the partitions we need for hybrid boot.
imgsize=`stat -f %z $NAME`
$MKIMG -s gpt \
    --capacity $imgsize \
    -b $OBJDIR/boot/pmbr \
    $espparam \
    -p freebsd-boot:="$OBJDIR/boot/isoboot" \
    -o hybrid.img

# Drop the PMBR, GPT, and boot code into the System Area of the ISO.
dd if=hybrid.img of=$NAME bs=32k count=1 conv=notrunc
rm -f hybrid.img
