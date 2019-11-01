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
import tempfile
import getpass
from utils import sh, sh_str, e, info, error, import_function


create_aux_files = import_function('create-release-distribution', 'create_aux_files')


def main():
    prod = e("${PRODUCTION}")
    if prod and prod.lower() == "yes":
        KEY_PASSWORD = e("${IX_KEY_PASSWORD}") or getpass.getpass("Enter Password: ")
    else:
        KEY_PASSWORD = ""
    changelog = e('${CHANGELOG}')
    info('Using ChangeLog: {0}', changelog)
    ssh = e('${UPDATE_USER}@${UPDATE_HOST}')
    sshopts = '-o SendEnv={KEY_PASSWORD} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    temp_dest = sh_str("ssh ${ssh} ${sshopts} mktemp -d /tmp/update-${PRODUCT}-XXXXXXXXX")
    temp_changelog = sh_str("ssh ${ssh} ${sshopts} mktemp /tmp/changelog-XXXXXXXXX")
    delta_count = e('${DELTAS}')

    if not temp_dest or not temp_changelog:
        error('Failed to create temporary directories on {0}', ssh)

    sh('rsync -vr -e "ssh ${sshopts}" ${BE_ROOT}/release/LATEST/ ${ssh}:${temp_dest}/')
    if changelog:
        cl_file = None
        if changelog == '-':
            print('Enter changelog, ^D to end:')
            cl_file = tempfile.NamedTemporaryFile(delete=False)
            cl_file.write(bytes(sys.stdin.read(), 'UTF-8'))
            cl_file.close()
            changelog = cl_file.name

        sh('scp ${sshopts} ${changelog} ${ssh}:${temp_changelog}')
        if cl_file is not None:
            os.remove(cl_file.name)

    sh(
        "echo ${KEY_PASSWORD} |",
        "ssh ${sshopts} ${ssh}",
        "/usr/local/bin/freenas-release",
        "-P ${PRODUCT}",
        "-D ${UPDATE_DB}",
        "--archive ${UPDATE_DEST}",
        "-K ${FREENAS_KEYFILE}",
        "-C ${temp_changelog}" if changelog else "",
        "--deltas ${delta_count}" if delta_count else "",
        "add ${temp_dest}"
    )

    sh("ssh ${sshopts} ${ssh} rm -rf ${temp_dest}")
    sh("ssh ${sshopts} ${ssh} rm -rf ${temp_changelog}")
    # This last line syncs up with the cdn
    # It is only done in the case of public facing update
    if e("${INTERNAL_UPDATE}").lower() == "no":
        sh("ssh ${sshopts} ${ssh} /usr/local/sbin/rsync-mirror.sh")


if __name__ == '__main__':
    info('Pushing upgrade packages to update server')
    main()
