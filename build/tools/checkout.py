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
from dsl import load_profile_config
from utils import sh, sh_str, info, debug, e, setfile, appendfile


dsl = load_profile_config()
manifest = {sh_str("git config --get remote.origin.url"): sh_str("git rev-parse --short HEAD")}


def checkout_repo(repo):
    os.chdir(e('${BE_ROOT}'))
    if os.path.isdir(os.path.join(repo['path'], '.git')):
        os.chdir(repo['path'])
        branch = sh_str('git rev-parse --abbrev-ref HEAD')
        if branch != repo['branch']:
            sh('git remote set-url origin', repo['url'])
            sh('git fetch origin')
            sh('git checkout', repo['branch'])

        sh('git pull --rebase')
    else:
        if e('${CHECKOUT_SHALLOW}'):
            sh('git clone', '-b', repo['branch'], '--depth', '1', repo['url'], repo['path'])
        else:
            sh('git clone', '-b', repo['branch'], repo['url'], repo['path'])
        os.chdir(repo['path'])

    if e('${CHECKOUT_TAG}'):
        sh('git checkout ${CHECKOUT_TAG}')
    elif 'commit' in repo:
        sh('git checkout', repo['commit'])

    manifest[repo['url']] = sh_str("git rev-parse --short HEAD")


def generate_manifest():
    sh('rm -f ${BE_ROOT}/repo-manifest')
    for k, v in manifest.items():
        appendfile('${BE_ROOT}/repo-manifest', e('${k} ${v}'))

if __name__ == '__main__':
    if not e('${SKIP_CHECKOUT}'):
        for i in dsl['repos']:
            if e('${CHECKOUT_ONLY}'):
                if i['name'] not in e('${CHECKOUT_ONLY}').split(','):
                    continue

            info('Checkout: {0} -> {1}', i['name'], i['path'])
            debug('Repository URL: {0}', i['url'])
            debug('Local branch: {0}', i['branch'])
            checkout_repo(i)

    generate_manifest()
    setfile('${BE_ROOT}/.pulled', e('${PRODUCT}'))
