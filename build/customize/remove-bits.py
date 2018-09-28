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


import sys
from utils import sh, e, info


def main(destdir):
    # Kill docs
    sh('rm -rf ${destdir}/usr/local/share/doc')
    sh('rm -rf ${destdir}/usr/local/share/gtk-doc')

    # Kill gobject introspection xml
    sh('rm -rf ${destdir}/usr/local/share/git-1.0')

    # Kill examples
    sh('rm -rf ${destdir}/usr/local/share/examples')
    sh('rm -rf ${destdir}/usr/share/me')

    # Kill sources of locale files
    sh("find ${destdir}/usr/local -type f -name '*.po' -delete")

    # Kill install leftover (#27013)
    sh('rm -rf ${destdir}/var/tmp/rc.conf.frenas')
    sh('rm -rf ${destdir}/var/tmp/freenas_config.md5')

    # magic.mgc is just a speed optimization
    sh('rm -f ${destdir}/usr/share/misc/magic.mgc')

    # If we are doing SDK build, we can stop here
    if e('${SDK}') == "yes":
        info('SDK: Skipping remove-bits...')
        return 0

    # Kill static libraries
    sh("find ${destdir}/usr/local \( -name '*.a' -or -name '*.la' \) -delete")
    sh("rm -rf ${destdir}/usr/lib/*.a")

    # Kill info
    sh('rm -rf ${destdir}/usr/local/info')

    # Kill .pyo files
    sh("find ${destdir}/usr/local \( -name '*.pyo' \) -delete")

    # We don't need python test in the image
    sh('rm -rf ${destdir}/usr/local/lib/python3.7/test')

    # Kill includes
    sh("find ${destdir}/usr/local/include \( \! -name 'pyconfig.h' \) -type f -delete")

if __name__ == '__main__':
    main(sys.argv[1])
