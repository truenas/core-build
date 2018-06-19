#!/usr/bin/env python3
#
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
from utils import e, info, debug, error, sh_str


def check_build_sanity():
    if len(e('${BUILD_ROOT}')) > 38:
        error("Current path too long ({0} characters) for nullfs mounts during build",
              len(os.getcwd()))

    #if e('${BE_ROOT}/objs/ports') in sh_str('mount'):
    #    error("You have dangling mounts inside {0}, did last build crash?", e('${BE_ROOT}'))


def check_port(name, port):
    debug('Checking for "{0}" command', name)
    for i in e('${PATH}').split(':'):
        if os.path.exists(e('${i}/${name}')):
            return

    error('Command {0} not found. Please run "pkg install {1}" or install from ports', name, port)


def check_port_version(name, port, version):
    debug('Checking for version {0} of {1}', version, name)
    install_ver = os.popen("""pkg info -q | awk -F- '/%s/ {print $2}'"""
                           """| awk -F. '/%s/ {print $2}'""" % (name, version)).read().strip()
    if version != install_ver:
        error('Wrong version of {0} installed:', port)


def check_port_byfile(name, port, fname):
    debug('Checking for "{0}"', name)
    if os.path.exists(fname):
        return

    error('{0} not found.  Please run "pkg install {1}" or install from ports', fname, port)


def check_build_tools():
    check_port('git', 'devel/git')
    check_port('pxz', 'archivers/pxz')
    check_port('python3', 'lang/python3')
    check_port('poudriere', 'ports-mgmt/poudriere-devel')
    check_port('gmake', 'devel/gmake')


if __name__ == '__main__':
    info('Checking build environment...')
    check_build_sanity()
    check_build_tools()
    info('Build environment is OK')
