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
import tempfile, shutil
from dsl import load_file
from utils import e, sh, import_function, env, info


dsl = load_file('${BUILD_CONFIG}/upgrade.pyd', os.environ)
create_aux_files = import_function('create-release-distribution', 'create_aux_files')


def stage_upgrade():
    sh('rm -rf ${UPGRADE_STAGEDIR}')
    sh('mkdir -p ${UPGRADE_STAGEDIR}')
    sh('cp -R ${OBJDIR}/packages/Packages ${UPGRADE_STAGEDIR}/')

    # Move any validation scripts back
    for v in "ValidateInstall", "ValidateUpdate":
        if os.path.exists(e('${UPGRADE_STAGEDIR}/Packages/${v}')):
            sh(e("mv ${UPGRADE_STAGEDIR}/Packages/${v} ${UPGRADE_STAGEDIR}/${v}"))
            
    # If RESTART is given, save that
    if env('RESTART'):
       sh('echo ${RESTART} > ${UPGRADE_STAGEDIR}/RESTART')

    # And if REBOOT is given, put that in FORCEREBOOT
    if env('REBOOT'):
       sh('echo ${REBOOT} > ${UPGRADE_STAGEDIR}/FORCEREBOOT')
    sh('rm -f ${BE_ROOT}/release/LATEST')
    sh('ln -sf ${UPGRADE_STAGEDIR} ${BE_ROOT}/release/LATEST')

def create_upgradefile():
    """
    Copy the manifest, and all other files, into a temp directory,
    then create a tarball from that.  We need to rename ${PRODUCT}-MANIFEST
    to simply MANIFEST, and all the Pakages files go into the base directory.
    We'll name the resulting file ${PRODUCT}-${VERSION}.tar
    """
    info("Creating update tar-file")
    temp_dir = tempfile.mkdtemp()
    source_dir = e("${UPGRADE_STAGEDIR}")
    for entry in os.listdir(source_dir):
        if entry == e("${PRODUCT}-MANIFEST"):
            shutil.copyfile(os.path.join(source_dir, entry),
                            os.path.join(temp_dir, "MANIFEST"))
        elif entry == "Packages":
            for pkgfile in os.listdir(os.path.join(source_dir, entry)):
                shutil.copyfile(os.path.join(source_dir, entry, pkgfile),
                                os.path.join(temp_dir, pkgfile))
        else:
            shutil.copyfile(os.path.join(source_dir, entry),
                            os.path.join(temp_dir, entry))
    sh("chmod 755 {0}".format(temp_dir))
    sh("tar -C {0} -cf {1} .".format(temp_dir, e("${BE_ROOT}/release/${PRODUCT}-${VERSION}-manual-update-unsigned.tar")))
    info("tar-file path: ${{BE_ROOT}}/release/${{PRODUCT}}-${{VERSION}}-manual-update-unsigned.tar")
    shutil.rmtree(temp_dir)

if __name__ == '__main__':
    stage_upgrade()
    create_aux_files(dsl, e('${UPGRADE_STAGEDIR}'))
    create_upgradefile()
