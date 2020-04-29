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
import re
import sys
from dsl import load_profile_config
from utils import sh, sh_str, info, debug, e, setfile, appendfile


def get_git_rev():
    """Return git revision.  Assumes $cwd is within the repository."""
    return sh_str("git rev-parse --short HEAD")


dsl = load_profile_config()
manifest = {sh_str("git config --get remote.origin.url"): get_git_rev()}


def is_git_repo(path, allow_bare=False):
    """Determine whether given path names a git repository."""
    # This is how git itself does it
    if os.path.exists(os.path.join(path, '.git', 'HEAD')):
        return True
    if allow_bare and os.path.exists(os.path.join(path, 'HEAD')):
        return True
    return False


def find_ref_clone(repo_name):
    """See if there's an existing clone to use as a reference."""
    git_ref_path = e('${GIT_REF_PATH}')
    if git_ref_path:
        for path in git_ref_path.split(':'):
            candidate = os.path.join(path, repo_name)
            if is_git_repo(candidate, allow_bare=True):
                return candidate
    return None


def get_latest_commit(repo, branch):
    output = sh_str('git ls-remote', repo, f'refs/heads/{branch}')
    commit = output.split()
    if commit and not re.search(r'^[a-f0-9]+$', commit[0]):
        return None
    return commit


def checkout_repo(cwd, repo):
    """Check out the given repository.

    Arguments:
        cwd -- start in this directory.
        repo -- gives 'name', 'path', 'branch', and 'url'
                (and optionally 'commit')

    We check out the given branch, unless ${CHECKOUT_TAG} is
    set (then we check out that value), or unless a 'commit'
    key is set (then we check out repo['commit']).

    If ${CHECKOUT_SHALLOW} is set, new clones are made with
    depth 1.

    If ${GIT_REF_PATH} is set, we can check for reference clones
    that may be available in that path (colon separated path
    as for normal Unix conventions).
    """

    buildenv_root = e('${BE_ROOT}')
    repo_name = repo['name']
    repo_path = repo['path']
    repo_url = repo['url']
    mirror_url = e(f'${{REPO_{repo_name.replace("-", "_").upper()}_URL}}')
    branch = e(f'${{{repo_name.replace("-", "_").upper()}_OVERRIDE}}') or repo['branch']

    if mirror_url:
        if get_latest_commit(mirror_url, branch) == get_latest_commit(repo_url, branch):
            info(f'Mirror {mirror_url} up-to-date with remote {repo_url}, using it')
            repo_url = mirror_url
        else:
            info(f'Mirror {mirror_url} does not match latest commit of {repo_url}, skipping it')

    # Search for a reference clone before changing directories
    # in case it's a relative path.
    os.chdir(cwd)
    refclone = find_ref_clone(repo_name)
    if refclone:
        refclone = os.path.abspath(refclone)

    os.chdir(buildenv_root)
    if is_git_repo(repo_path):
        os.chdir(repo_path)
        current_branch = sh_str('git rev-parse --abbrev-ref HEAD')
        current_origin = sh_str('git remote get-url origin')
        if current_branch != branch or current_origin != repo_url:
            # (re)setting origin is a bit rude if someone had
            # carefully set their own variant, but oh well.
            sh('git remote set-url origin', repo_url)
            sh('git fetch origin')
            sh('git checkout', branch)

        # git pull --rebase exhibits bad behavior in git 2.8.x and
        # early 2.9.x, leaving dead lock files.  This is an attempted
        # work-around - it should behave the same, perhaps minus
        # internal git bugs.
        sh('git fetch && git rebase')
    else:
        if e('${CHECKOUT_SHALLOW}'):
            sh('git clone -b', branch, '--depth 1', repo_url, repo_path)
        else:
            # Should we have an option to add --dissociate?
            if refclone:
                sh('git clone --reference', refclone,
                   '-b', branch, repo_url, repo_path)
            else:
                sh('git clone -b', branch, repo_url, repo_path)
        os.chdir(repo_path)

    if e('${CHECKOUT_TAG}'):
        sh('git checkout ${CHECKOUT_TAG}')
    elif 'commit' in repo:
        sh('git checkout', repo['commit'])

    manifest[repo_url] = get_git_rev()


def generate_manifest():
    sh('rm -f ${BE_ROOT}/repo-manifest')
    for k, v in manifest.items():
        appendfile('${BE_ROOT}/repo-manifest', e('${k} ${v}'))


def main():
    if not e('${SKIP_CHECKOUT}'):
        cwd = os.getcwd()
        checkout_only = e('${CHECKOUT_ONLY}')
        checkout_exclude = e('${CHECKOUT_EXCLUDE}')

        if checkout_only:
            checkout_only = checkout_only.split(',')

        if checkout_exclude:
            checkout_exclude = checkout_exclude.split(',')

        for i in dsl['repos']:
            if checkout_only and i['name'] not in checkout_only:
                continue

            if checkout_exclude and i['name'] in checkout_exclude:
                continue

            info('Checkout: {0} -> {1}', i['name'], i['path'])
            debug('Repository URL: {0}', i['url'])
            debug('Local branch: {0}', i['branch'])
            checkout_repo(cwd, i)

    generate_manifest()
    setfile('${BE_ROOT}/.pulled', e('${PRODUCT}'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
