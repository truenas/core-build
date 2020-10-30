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
import json
import subprocess
from dsl import load_file, load_profile_config
from utils import e, glob, objdir, sh, sh_str, readfile, setfile, template, info


dsl = load_file('${BUILD_CONFIG}/release.pyd', os.environ)
url = dsl.url


def stage_non_installed_ports():

    """
    If a port was given the `install` key and it was
    set to False, then the port was not installed but
    we still should save the associated *.txz file in
    the final release directory.
    """

    config = load_profile_config()
    glob_pattern = '/*.txz'

    non_installed_ports = []
    for i in config.ports:
        if isinstance(i, dict) and not i.get('install', True):
            if 'package' in i:
                non_installed_ports.append(i.package)
            else:
                non_installed_ports.append(i.name)

    if non_installed_ports:
        sh('mkdir -p ${RELEASE_STAGEDIR}/${BUILD_ARCH_SHORT}/${NON_INSTALLED_DIR}')
        pkgdir = subprocess.run(
            ['find', objdir('ports/data/packages'), '-name', 'All', '-type', 'd'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if pkgdir.stdout:
            pkgdir = pkgdir.stdout.decode().strip()

            for i in non_installed_ports:
                # port name will have the directory it resides in
                # so make sure to remove it if it's there
                if '/' in i:
                    i = i.split('/')[1]

                for t in glob(pkgdir + glob_pattern):
                    pkg = t.split('/')[-1]
                    if pkg.startswith(i):
                        sh('cp ${t} ${RELEASE_STAGEDIR}/${BUILD_ARCH_SHORT}/${NON_INSTALLED_DIR}')


def stage_release():
    sh('mkdir -p ${RELEASE_STAGEDIR}/${BUILD_ARCH_SHORT}')
    releases = [e('${OBJDIR}/${NAME}.${ext}') for ext in dsl.formats]
    for path in releases:
        if os.path.exists(path):
            info(e('Moving ${path} artifact to release directory'))
            sh('mv ${path} ${RELEASE_STAGEDIR}/${BUILD_ARCH_SHORT}/')
            sh('mv ${path}.sha256 ${RELEASE_STAGEDIR}/${BUILD_ARCH_SHORT}/')
            info('ISO path: ${{RELEASE_STAGEDIR}}/${{BUILD_ARCH_SHORT}}')


def get_aux_files_desc():
    for aux in dsl.aux_files:
        name = aux.name
        # Please note that the aux.source is not the one in the
        # release stagedir but if it did not exist in the first place
        # then create_aux_files function would not have copied it over.
        if os.path.exists(aux.source):
            yield {
                'filename': name,
                'hash': sh_str("sha256 -q ${RELEASE_STAGEDIR}/${name}"),
            }
        else:
            continue


def get_image_files_desc():
    for ext in dsl.formats:
        path = e('${RELEASE_STAGEDIR}/${BUILD_ARCH_SHORT}/${NAME}.${ext}')
        filename = os.path.basename(path)
        if os.path.exists(path):
            yield {
                'filename': filename,
                'type': ext,
                'hash': sh_str("sha256 -q ${path}"),
                'url': e("${url}/${filename}")
            }


def create_aux_files(dsl, dest):
    for aux in dsl.aux_files:
        if not os.path.exists(aux.source):
            continue

        if aux.get('template'):
            f = template(aux.source)
        else:
            f = readfile(aux.source)

        name = aux.name
        setfile('${dest}/${name}', f)


def create_json():
    version = e('${VERSION}').split('-')[0]
    json_file = {
        'name': e('${PRODUCT}'),
        'version': e('${version}'),
        'type': e('${BUILD_TYPE}'),
        'date': e('${BUILD_TIMESTAMP}'),
        'aux_files': list(get_aux_files_desc()),
        'arch': {
            e('${BUILD_ARCH}'): list(get_image_files_desc())
        }
    }

    f = open(e("${RELEASE_STAGEDIR}/CHECKSUMS.json"), 'a')
    json.dump(json_file, f, indent=4)
    f.close()


if __name__ == '__main__':
    stage_release()
    stage_non_installed_ports()
    create_aux_files(dsl, e('${RELEASE_STAGEDIR}'))
    create_json()
