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
import ipaddress
import subprocess
import threading
import time
from dhcp.server import Server
from dhcp.lease import Lease
from dsl import load_file, load_profile_config
from utils import sh, sh_str, sh_spawn, info, objdir, e


load_profile_config()
load_file(e('${BUILD_ROOT}/tests/freenas/config.pyd'), os.environ)
destdir = objdir('tests')
venvdir = objdir('tests/venv')
isopath = objdir('${NAME}.iso')
tapdev = None
dhcp_server = None
ready = threading.Event()


def cleanup():
    sh('bhyvectl --destroy --vm=${VM_NAME}', nofail=True)


def setup_files():
    sh('mkdir -p ${destdir}')
    sh('truncate -s 8G ${destdir}/boot.img')
    sh('truncate -s 20G ${destdir}/hd1.img')
    sh('truncate -s 20G ${destdir}/hd2.img')


def alloc_network():
    global tapdev

    tapdev = sh_str('ifconfig tap create')
    info('Using tap device {0}', tapdev)


def setup_network():
    info('Configuring VM networking')
    sh('ifconfig ${tapdev} inet ${HOST_IP} ${NETMASK} up')


def cleanup_network():
    sh('ifconfig ${tapdev} destroy')


def setup_dhcp_server():
    global dhcp_server

    def dhcp_request(mac, hostname):
        info('DHCP request from {0} ({1})'.format(hostname, mac))
        lease = Lease()
        lease.client_mac = mac
        lease.client_ip = ipaddress.ip_address(e('${FREENAS_IP}'))
        lease.client_mask = ipaddress.ip_address(e('${NETMASK}'))
        ready.set()
        return lease

    dhcp_server = Server()
    dhcp_server.server_name = 'FreeNAS_test_env'
    dhcp_server.on_request = dhcp_request
    dhcp_server.start(tapdev, ipaddress.ip_address(e('${HOST_IP}')))
    threading.Thread(target=dhcp_server.serve, daemon=True).start()
    info('Started DHCP server on {0}', tapdev)

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

    ready.wait()
    time.sleep(60)
    info('VM middleware is ready')

    proc = subprocess.Popen(
        [
            e('${venvdir}/bin/python'),
            e('${BUILD_ROOT}/tests/freenas/main.py'),
            '-a', e('${FREENAS_IP}'),
            '-u', 'root',
            '-p', 'abcd1234'
        ]
    )

    proc.wait()

    vm_proc.terminate()
    vm_proc.wait()


if __name__ == '__main__':
    info('Starting up test schedule')
    cleanup()
    alloc_network()
    setup_files()
    setup_network()
    setup_dhcp_server()
    do_install()
    setup_network()
    do_run()
    cleanup_network()
