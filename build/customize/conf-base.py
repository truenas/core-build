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

from utils import sh, setfile


def main():
    sh('mkdir -p ${WORLD_DESTDIR}/conf/base/etc')
    sh('mkdir -p ${WORLD_DESTDIR}/conf/base/etc/local')
    sh('mkdir -p ${WORLD_DESTDIR}/conf/base/var')
    sh('mkdir -p ${WORLD_DESTDIR}/conf/base/mnt')
    sh('touch ${WORLD_DESTDIR}/etc/diskless')
    sh('cp -a ${WORLD_DESTDIR}/etc/ ${WORLD_DESTDIR}/conf/base/etc')
    sh('cp -a ${WORLD_DESTDIR}/usr/local/etc/ ${WORLD_DESTDIR}/conf/base/etc/local')
    sh('rm -rf ${WORLD_DESTDIR}/usr/local/etc')
    sh('ln -s /etc/local ${WORLD_DESTDIR}/usr/local/etc')
    sh('cp -a ${WORLD_DESTDIR}/var/ ${WORLD_DESTDIR}/conf/base/var')

    setfile('${WORLD_DESTDIR}/conf/base/var/md_size', '')
    setfile('${WORLD_DESTDIR}/conf/base/etc/md_size', '65535')
    setfile('${WORLD_DESTDIR}/conf/base/mnt/md_size', '8192')

    # Symlink /tmp to /var/tmp
    sh('rm -rf ${WORLD_DESTDIR}/tmp')
    sh('ln -s /var/tmp ${WORLD_DESTDIR}/tmp')

    # Make sure .rnd points to tmpfs.
    # Some daemons starting at boot time will try to write that file
    # because of $HOME/.rnd is the default path and HOME=/ defined in /etc/rc
    # See #23304
    sh('ln -s /var/tmp/.rnd ${WORLD_DESTDIR}/.rnd')
    sh('touch ${WORLD_DESTDIR}/conf/base/var/tmp/.rnd')

    sh('ln -s -f /usr/local/bin/ntfs-3g ${WORLD_DESTDIR}/sbin/mount_ntfs')


if __name__ == '__main__':
    main()
