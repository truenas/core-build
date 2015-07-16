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
import sys
import glob
from utils import sh, sh_str, e, setup_env, info


def main():
    # name = os.path.basename(e('${RELEASE_STAGEDIR}'))
    # sh('cp -r ${RELEASE_STAGEDIR} ${IX_INTERNAL_PATH}/${name}')
    ref_date = 0
    rel_dir = ''
    dirstring = e('${BE_ROOT}/release/${PRODUCT}')
    for x in glob.glob("{0}*".format(dirstring)):
        if e('${BUILD_ARCH_SHORT}') not in os.listdir(x):
            continue

        if os.lstat(x).st_ctime > ref_date:
            ref_date = os.lstat(x).st_ctime
            rel_dir = x
    name = os.path.basename(rel_dir)
    sh('cp -r ${rel_dir} ${IX_INTERNAL_PATH}/${name}')


if __name__ == '__main__':
    info('Pushing release to internal storage')
    main()
