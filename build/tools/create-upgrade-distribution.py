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
from dsl import load_file
from utils import e, sh, import_function, env


dsl = load_file('${BUILD_CONFIG}/upgrade.pyd', os.environ)
create_aux_files = import_function('create-release-distribution', 'create_aux_files')


def stage_upgrade():
    sh('rm -rf ${UPGRADE_STAGEDIR}')
    sh('mkdir -p ${UPGRADE_STAGEDIR}')
    sh('cp -R ${OBJDIR}/packages/Packages ${UPGRADE_STAGEDIR}/')

    # If an update validation script is given, copy that
    if os.path.exists(e('${PROFILE_ROOT}/ValidateUpdate')):
        sh('cp ${PROFILE_ROOT}/ValidateUpdate ${UPGRADE_STAGEDIR}/ValidateUpdate')
    if os.path.exists(e('${PROFILE_ROOT}/ValidateInstall')):
        sh('cp ${PROFILE_ROOT}/ValidateUpdate ${UPGRADE_STAGEDIR}/ValidateInstall')
        
    # Allow the environment to over-ride it -- /dev/null or empty string means
    # don't have one
    if env('VALIDATE_UPDATE'):
        if env('VALIDATE_UPDATE') not in ("/dev/null", ""):
            sh('cp ${VALIDATE_UPDATE} ${UPGRADE_STAGEDIR}/ValidateUpdate')
        else:
            sh('rm -f ${UPGRADE_STAGEDIR}/ValidateUpdate')
    if env('VALIDATE_INSTALL'):
        if env('VALIDATE_INSTALL') not in ("/dev/null", ""):
            sh('cp ${VALIDATE_INSTALL} ${UPGRADE_STAGEDIR}/ValidateInstall')
        else:
            sh('rm -f ${UPGRADE_STAGEDIR}/ValidateInstall')

    # If RESTART is given, save that
    if env('RESTART'):
       sh('echo ${RESTART} > ${UPGRADE_STAGEDIR}/RESTART')

    # And if REBOOT is given, put that in FORCEREBOOT
    if env('REBOOT'):
       sh('echo ${REBOOT} > ${UPGRADE_STAGEDIR}/FORCEREBOOT')
    sh('rm -f ${BE_ROOT}/release/LATEST')
    sh('ln -sf ${UPGRADE_STAGEDIR} ${BE_ROOT}/release/LATEST')


if __name__ == '__main__':
    stage_upgrade()
    create_aux_files(dsl, e('${UPGRADE_STAGEDIR}'))
