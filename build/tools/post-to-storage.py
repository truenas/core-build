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
import glob
from utils import sh, e, info, error


def main():
    ref_date = 0
    rel_dir = ''
    dirstring = e('${BE_ROOT}/release/${PRODUCT}')
    for x in glob.glob("{0}*".format(dirstring)):
        if os.path.isdir(e('${x}/${BUILD_ARCH_SHORT}')) and os.lstat(x).st_ctime > ref_date:
            ref_date = os.lstat(x).st_ctime
            rel_dir = x

    if not rel_dir:
        error('Release not found')

    if e('${BUILD_TYPE}').lower() in ["master", "stable", "freebsd-stable", "freebsd-head"]:
        appending_path = e('${VERSION_NUMBER}/${BUILD_TYPE}')
    else:
        appending_path = e('${VERSION_NUMBER}')

    internal_path = os.path.join(e('${IX_INTERNAL_PATH_PREFIX}'), appending_path)
    if os.path.exists(internal_path):
        rel_dir_base = os.path.basename(rel_dir)
        target_path = os.path.join(internal_path, rel_dir_base)
        sh('cp -r ${rel_dir} ${target_path}')
        sh('ln -shf ${rel_dir_base} ${internal_path}/latest')


if __name__ == '__main__':
    info('Pushing release to internal storage')
    main()
