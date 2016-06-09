#!/usr/bin/env python2.7
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
import errno
from utils import sh, e, info, objdir, sha256, is_elf


output = objdir('${NAME}.debug.txz')


def main():
    sh('rm -rf ${DEBUG_WORLD}')
    sh('mkdir -p ${DEBUG_WORLD}')

    info('Saving debug information in ${{DEBUG_WORLD}}')

    for root, dirs, files in os.walk(e('${WORLD_DESTDIR}/')):
        for name in files:
            filename = os.path.join(root, name)
            relpath = os.path.relpath(filename, e('${WORLD_DESTDIR}'))
            destpath = os.path.join(e('${DEBUG_WORLD}'), relpath)

            if os.path.splitext(name)[1] == '.ko':
                continue

            if relpath.startswith(('boot', 'usr/local/lib/grub')):
                continue

            if not is_elf(filename):
                continue

            try:
                os.makedirs(os.path.dirname(destpath))
            except OSError as err:
                if err.errno != errno.EEXIST:
                    raise

            # We need to remove any flags on protected files and restore
            # them after stripping
            flags = os.stat(filename).st_flags
            os.chflags(filename, 0)

            if not relpath.startswith('rescue'):
                sh('objcopy --only-keep-debug ${filename} ${destpath}.debug')
                sh('objcopy --strip-unneeded ${filename}')
                sh('objcopy --add-gnu-debuglink="${destpath}.debug" ${filename}', log='/dev/null', nofail=True)
            else:
                sh('strip ${filename}')

            os.chflags(filename, flags)


def create_package():
    if os.path.exists('/usr/local/bin/pigz'):
        sh('tar -C ${DEBUG_ROOT} -cvf - . | /usr/local/bin/pigz -c > ${output}', log='/dev/null')
    else:
        sh('tar -C ${DEBUG_ROOT} -cvJf ${output} .', log='/dev/null')

    sha256(output)


if __name__ == '__main__':
    if e("${BUILD_DEBUG_PACKAGE}") not in ("no", "NO"):
        main()
        create_package()
