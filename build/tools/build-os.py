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
from dsl import load_profile_config
from utils import sh, sh_str, env, e, objdir, info, debug, pathjoin


config = load_profile_config()
arch = env('TARGET_ARCH', 'amd64')
makeconfbuild = objdir('make-build.conf')
kernconf = objdir(e('${KERNCONF}'))
kernconf_debug = objdir(e('${KERNCONF}-DEBUG'))
kernlog = objdir('logs/buildkernel')
kerndebuglog = objdir('logs/buildkernel-debug')
worldlog = objdir('logs/buildworld')
makejobs = None


def calculate_make_jobs():
    global makejobs

    # We use number of CPUs + 1, to have
    # some overlap with I/O overhead.
    cores = sh_str('sysctl -n hw.ncpu')
    if not cores:
        cores = 2

    makejobs = os.environ.get("BUILDWORLD_JOBS", int(cores) + 1)
    debug('Using {0} make jobs', makejobs)


def create_make_conf_build():
    conf = open(makeconfbuild, 'w')
    for k, v in config['make_conf_build'].items():
        conf.write('{0}={1}\n'.format(k, v))
    conf.close()
    conf = open(objdir('make-jail.conf'), 'w')
    for k, v in config['make_conf_build'].items():
        conf.write('{0}={1}\n'.format(k, v))
    for k, v in config['make_conf_jail'].items():
        conf.write('{0}={1}\n'.format(k, v))
    conf.close()
    conf = open(objdir('make-run.conf'), 'w')
    for k, v in config['make_conf_build'].items():
        conf.write('{0}={1}\n'.format(k, v))
    for k, v in config['make_conf_run'].items():
        conf.write('{0}={1}\n'.format(k, v))
    conf.close()
    conf = open(objdir('make-boot.conf'), 'w')
    for k, v in config['make_conf_build'].items():
        conf.write('{0}={1}\n'.format(k, v))
    for k, v in config['make_conf_run'].items():
        conf.write('{0}={1}\n'.format(k, v))
    for k, v in config['make_conf_boot'].items():
        conf.write('{0}={1}\n'.format(k, v))
    conf.close()


def create_kernel_config():
    with open(kernconf, 'w') as f:
        with open(pathjoin('${PROFILE_ROOT}', config['kernel_config']), 'r') as f2:
            f.write(f2.read())

    with open(kernconf_debug, 'w') as f:
        with open(pathjoin('${PROFILE_ROOT}', config['kernel_config']), 'r') as f2:
            f.write(f2.read())

        with open(os.path.join(
            os.path.dirname(pathjoin('${PROFILE_ROOT}', config['kernel_config'])),
            'DEBUG'
        ), 'r') as f2:
            f.write(f2.read())


def buildkernel(kconf, modules, log):
    modules = ' '.join(modules)
    info('Building kernel {0} from {1}', kconf, e('${OS_ROOT}'))
    info('Log file: {0}', log)
    debug('Kernel configuration file: {0}', kernconf)
    debug('Selected modules: {0}', modules)

    sh(
        "env -u DEBUG -u MAKEFLAGS MAKEOBJDIRPREFIX=${OBJDIR}",
        "make",
        "-j {0}".format(makejobs),
        "-C ${OS_ROOT}",
        "NO_KERNELCLEAN=YES",
        "KERNCONF={0}".format(kconf),
        "__MAKE_CONF={0}".format(makeconfbuild),
        "MODULES_OVERRIDE='{0}'".format(modules),
        "buildkernel",
        log=log
    )


def buildworld():
    info('Building world from ${{OS_ROOT}}')
    info('Log file: {0}', worldlog)
    debug('World make.conf: {0}', makeconfbuild)

    sh(
        "env -u DEBUG -u MAKEFLAGS MAKEOBJDIRPREFIX=${OBJDIR}",
        "make",
        "-j {0}".format(makejobs),
        "-C ${OS_ROOT}",
        "__MAKE_CONF={0}".format(makeconfbuild),
        "NOCLEAN=YES",
        "buildworld",
        log=worldlog
    )


def installworld(destdir, worldlog, distriblog, conf="build"):
    info('Installing world in {0}', destdir)
    info('Log file: {0}', worldlog)
    makeconf = objdir("make-${conf}.conf")
    sh(
        "env MAKEOBJDIRPREFIX=${OBJDIR}",
        "make",
        "-C ${OS_ROOT}",
        "installworld",
        "DESTDIR=${destdir}",
        "__MAKE_CONF=${makeconf}",
        log=worldlog
    )

    info('Creating distribution in {0}', destdir)
    info('Log file: {0}', distriblog)
    sh(
        "env MAKEOBJDIRPREFIX=${OBJDIR}",
        "make",
        "-C ${OS_ROOT}",
        "distribution",
        "DESTDIR=${destdir}",
        "__MAKE_CONF=${makeconf}",
        log=distriblog
    )


def installkernel(kconf, destdir, log, kodir=None, modules=None, conf="build"):
    info('Installing kernel in {0}', log)
    info('Log file: {0}', log)
    if modules is None:
        modules = config['kernel_modules']
    if kodir is None:
        kodir = "/boot/kernel"
    makeconf = objdir("make-${conf}.conf")
    modules = ' '.join(modules)
    sh(
        "env MAKEOBJDIRPREFIX=${OBJDIR}",
        "make",
        "-C ${OS_ROOT}",
        "installkernel",
        "DESTDIR=${destdir}",
        "KERNCONF={0}".format(kconf),
        "KODIR={0}".format(kodir),
        "__MAKE_CONF=${makeconf}",
        "MODULES_OVERRIDE='{0}'".format(modules),
        log=log
    )

    # Saving the SDK sources
    if e('${SDK}') == "yes":
        info('SDK: Saving FreeBSD sources to src.txz...')
        sh('tar cJf ${BE_ROOT}/src.txz --exclude .git -C ${OS_ROOT} .')


calculate_make_jobs()


if __name__ == '__main__':
    if env('SKIP_OS'):
        info('Skipping buildworld & buildkernel as instructed by setting SKIP_OS')
        sys.exit(0)

    create_make_conf_build()
    create_kernel_config()
    buildworld()
    buildkernel(e('${KERNCONF}'), config['kernel_modules'], kernlog)
    buildkernel(e('${KERNCONF}-DEBUG'), config['kernel_modules'], kerndebuglog)
