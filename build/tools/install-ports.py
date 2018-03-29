#!/usr/bin/env python3
#+
# Copyright 2015 iXsystems, Inc.
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
#####################################################################


import os
import sys
import glob
from dsl import load_profile_config
from utils import (
    sh, objdir, info, error, e, on_abort,
    chroot, get_port_names, readfile
)


config = load_profile_config()
logfile = objdir('logs/pkg-install')


def mount_packages():
    on_abort(umount_packages)
    jailname = readfile(e('${OBJDIR}/jailname'))
    sh('mkdir -p ${WORLD_DESTDIR}/usr/ports/packages')
    sh('mount -t nullfs ${OBJDIR}/ports/data/packages/${jailname}-p ${WORLD_DESTDIR}/usr/ports/packages')


def fetch_binary_packages():
    if e('${SKIP_PACKAGES_FETCH}'):
        return

    for i in config.binary_packages:
        _, name = os.path.split(i)

        if os.path.exists(e('${WORLD_DESTDIR}/usr/ports/packages/${name}')):
            continue

        info('Fetching package {0}', name)
        sh('fetch ${i} -o ${WORLD_DESTDIR}/usr/ports/packages/')


def umount_packages():
    sh('umount -f ${WORLD_DESTDIR}/usr/ports/packages')
    on_abort(None)

    # If doing a SDK build, we can nuke the local.conf and enable FreeBSD pkg
    if e('${SDK}') == "yes":
        info('SDK: Enabling pkgng repo')
        sh('sed -i "" "s|: no|: yes|g" ${WORLD_DESTDIR}/usr/local/etc/pkg/repos/FreeBSD.conf')
        sh('rm ${WORLD_DESTDIR}/usr/local/etc/pkg/repos/local.conf')


def create_pkgng_configuration():
    sh('mkdir -p ${WORLD_DESTDIR}/usr/local/etc/pkg/repos')
    for i in glob.glob(e('${BUILD_CONFIG}/templates/pkg-repos/*')):
        fname = os.path.basename(i)
        sh(e('cp ${i} ${WORLD_DESTDIR}/usr/local/etc/pkg/repos/${fname}'))


def install_ports():
    pkgs = ' '.join(get_port_names(config.ports))
    sh('mount -t devfs devfs ${WORLD_DESTDIR}/dev')
    sh('mount -t fdescfs fdescfs ${WORLD_DESTDIR}/dev/fd')
    err = chroot('${WORLD_DESTDIR}', 'env ASSUME_ALWAYS_YES=yes pkg install -r local -f ${pkgs}', log=logfile, logtimestamp=True, nofail=True)
    sh('umount -f ${WORLD_DESTDIR}/dev/fd')
    sh('umount -f ${WORLD_DESTDIR}/dev')

    if not os.path.isdir(e('${WORLD_DESTDIR}/data')) or err != 0:
        error('Packages installation failed, see log file {0}', logfile)

    # If we are SDK'ing lets save the ports.txz file
    if e('${SDK}') == "yes":
        sh('mkdir -p ${WORLD_DESTDIR}/sdk')
        info('Saving ports.txz to /sdk/')
        sh('cp ${BE_ROOT}/ports.txz ${WORLD_DESTDIR}/sdk/ports.txz')
        info('Saving src.txz to /sdk/')
        sh('cp ${BE_ROOT}/src.txz ${WORLD_DESTDIR}/sdk/src.txz')


def install_binary_packages():
    for i in config.binary_packages:
        _, name = os.path.split(i)
        path = e('/usr/ports/packages/${name}')
        chroot('${WORLD_DESTDIR}', 'env ASSUME_ALWAYS_YES=yes pkg -o DEBUG_LEVEL=3 install -f ${path}', log=logfile)


if __name__ == '__main__':
    if e('${SKIP_PORTS_INSTALL}'):
        info('Skipping ports install as instructed by setting SKIP_PORTS_INSTALL')
        sys.exit(0)

    info('Installing ports')
    info('Log file: {0}', logfile)
    mount_packages()
    fetch_binary_packages()
    create_pkgng_configuration()
    install_ports()
    install_binary_packages()
    umount_packages()
