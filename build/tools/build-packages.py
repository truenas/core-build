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
import time
import hashlib
from dsl import load_profile_config
from utils import sh, sh_str, e, setup_env, objdir, info, debug, error


config = load_profile_config()
tooldir = objdir('pkgtools')
pkgdir = objdir('packages')
pkgtoolslog = objdir('logs/build-pkgtools')
pkgversion = ''
sequence = ''


def read_repo_manifest():
    global pkgversion
    global sequence

    versions = []
    f = open(e("${BE_ROOT}/repo-manifest"))
    o = open(e("${BE_ROOT}/objs/world/etc/repo-manifest"), "w")

    for i in f:
        versions.append(i.split()[1])
        o.write(i)

    pkgversion = hashlib.md5('-'.join(versions)).hexdigest()
    sequence = sh_str('git show -s --format=%ct')


def build_pkgtools():
    info('Building freenas-pkgtools')
    info('Log file: {0}', pkgtoolslog)

    sh(
        "env MAKEOBJDIRPREFIX=${OBJDIR}",
        "make -C ${SRC_ROOT}/freenas-pkgtools obj all install DESTDIR=${tooldir} PREFIX=/usr/local",
        log=pkgtoolslog
    )

    sh(
        "env MAKEOBJDIRPREFIX=${OBJDIR}",
        "make -C ${SRC_ROOT}/freenas-pkgtools obj all install DESTDIR=${WORLD_DESTDIR} PREFIX=/usr/local",
        log=pkgtoolslog
    )


def build_packages():
    retval = []
    info('Building packages')
    sh('rm -rf ${pkgdir}/Packages')
    sh('mkdir -p ${pkgdir}/Packages')
    for i in config['packages']:
        template = i['template']
        name = i['name']
        pkg_file_name = e('${pkgdir}/Packages/${name}-${VERSION}-${pkgversion}.tgz')
        sh(
            "${tooldir}/usr/local/bin/create_package",
            "-R ${WORLD_DESTDIR}",
            "-T ${template}",
            "-N ${name}",
            "-V ${VERSION}-${pkgversion}",
            "${pkg_file_name}" )
        retval.append(pkg_file_name)
    return retval


def create_manifest(pkgs):
    info('Creating package manifests')
    date = int(time.time())
    train = e('${TRAIN}') or 'FreeNAS'
    sh(
        "env PYTHONPATH=${tooldir}/usr/local/lib",
        "${tooldir}/usr/local/bin/create_manifest",
        "-P ${pkgdir}/Packages",
        "-S ${sequence}",
        "-o ${pkgdir}/${PRODUCT}-${sequence}",
        "-R ${PRODUCT}-${VERSION}",
        "-T ${train}",
        "-t ${date}",
        *pkgs
    )

    sh('ln -sf ${PRODUCT}-${sequence} ${pkgdir}/${PRODUCT}-MANIFEST')

if __name__ == '__main__':
    if e('${SKIP_PACKAGES}'):
        info('Skipping build of following packages: ${SKIP_PACKAGES}')
    read_repo_manifest()
    build_pkgtools()
    pkg_list = build_packages()
    create_manifest(pkg_list)
