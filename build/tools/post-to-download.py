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
from utils import sh, sh_str, e, setup_env, info, error


def main():
    user = sh_str('id -un')
    if user == 'root':
        user = 'jkh'

    # sh('ssh ${user}@${DOWNLOAD_HOST} rm -rf ${DOWNLOAD_TARGETDIR}')
    # sh('ssh ${user}@${DOWNLOAD_HOST} mkdir -p ${DOWNLOAD_TARGETDIR}')
    # sh('scp -pr ${RELEASE_STAGEDIR}/* ${user}@${DOWNLOAD_HOST}:${DOWNLOAD_TARGETDIR}/')
    ref_date = 0
    rel_dir = ''
    dirstring = e('${BE_ROOT}/release/${PRODUCT}')
    for x in glob.glob("{0}*".format(dirstring)):
        if e('${BUILD_ARCH_SHORT}') not in os.listdir(x):
            continue

        if os.lstat(x).st_ctime > ref_date:
            ref_date = os.lstat(x).st_ctime
            rel_dir = x

    if not rel_dir:
        error('Release not found')

    if e('${BUILD_TYPE}').lower() in ["master", "stable"]:
        buildtimestamp = os.path.basename(rel_dir).split("-")[-1]
        downloadtargetdir = e('${DOWNLOAD_BASEDIR}/${MILESTONE}/${buildtimestamp}')
    else:
        downloadtargetdir = e('${DOWNLOAD_TARGETDIR}')
    sh('ssh ${user}@${DOWNLOAD_HOST} rm -rf ${downloadtargetdir}')
    sh('ssh ${user}@${DOWNLOAD_HOST} mkdir -p ${downloadtargetdir}')
    sh('scp -pr ${rel_dir}/* ${user}@${DOWNLOAD_HOST}:${downloadtargetdir}/')
    info('Synchronizing download server to CDN')
    sh('ssh ${user}@${DOWNLOAD_HOST} /usr/local/sbin/rsync-mirror.sh')


if __name__ == '__main__':
    info('Pushing release to download server')
    main()
