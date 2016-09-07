#+
# Copyright 2016 iXsystems, Inc.
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import os
import subprocess
from dsl import load_file, load_profile_config
from utils import sh, sh_str, sh_spawn, info, objdir, e


load_profile_config()
load_file(e('${BUILD_ROOT}/tests/freenas/config.pyd'), os.environ)
destdir = objdir('tests')
isopath = objdir('${NAME}.iso')
tapdev = None


def cleanup():
    sh('bhyvectl --destroy --vm=${VM_NAME}', nofail=True)


def setup_files():
    sh('mkdir -p ${destdir}')
    sh('truncate -s 8G ${destdir}/boot.img')
    sh('truncate -s 20G ${destdir}/hd1.img')
    sh('truncate -s 20G ${destdir}/hd2.img')


def setup_network():
    global tapdev

    info('Configuring VM networking')
    tapdev = sh_str('ifconfig tap create')
    info('Using tap device {0}', tapdev)
    sh('ifconfig ${tapdev} inet ${HOST_IP} ${NETMASK} up')


def do_install():
    info('Starting up VM for unattended install')
    vm_proc = sh_spawn(
        'bhyve -m ${MEMSIZE} -c ${CORES} -A -H -P',
        '-s 3:0,ahci-hd,${destdir}/boot.img',
        '-s 4:0,ahci-hd,${destdir}/hd1.img',
        '-s 5:0,ahci-hd,${destdir}/hd2.img',
        '-s 6:0,ahci-cd,${isopath}',
        '-s 7:0,virtio-net,${tapdev}',
        '-s 8:0,fbuf,tcp=5900,w=1024,h=768',
        '-s 31,lpc',
        '-l bootrom,/usr/local/share/uefi-firmware/BHYVE_UEFI.fd',
        '${VM_NAME}'
    )

    try:
        vm_proc.wait(timeout=3600)
    except subprocess.TimeoutExpired:
        fail('Install timed out after 1 hour')


def do_run():
    info('Starting up VM for testing')
    vm_proc = sh_spawn(
        'bhyve -m ${MEMSIZE} -c ${CORES} -A -H -P',
        '-s 3:0,ahci-hd,${destdir}/boot.img',
        '-s 4:0,ahci-hd,${destdir}/hd1.img',
        '-s 5:0,ahci-hd,${destdir}/hd2.img',
        '-s 6:0,virtio-net,${tapdev}',
        '-s 7:0,fbuf,tcp=5900,w=1024,h=768',
        '-s 31,lpc',
        '-l bootrom,/usr/local/share/uefi-firmware/BHYVE_UEFI.fd',
        '${VM_NAME}'
    )

    vm_proc.wait()


if __name__ == '__main__':
    info('Starting up test schedule')
    cleanup()
    setup_files()
    setup_network()
    do_install()
    do_run()