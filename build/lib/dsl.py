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


class ConfigArray(list):
    def __iadd__(self, other):
        if not isinstance(other, list):
            self.append(other)
            return self

        return super(ConfigArray, self).__iadd__(other)

    def where(self, **predicates):
        for i in self:
            found = True
            for k, v in predicates.items():
                if i[k] != v:
                    found = False
                    break

            if found:
                return i

        return None


class GlobalsWrapper(dict):
    def __init__(self, env, filename):
        super(GlobalsWrapper, self).__init__()
        self.dict = {}
        self.filename = filename
        self.env = env

    def __getitem__(self, item):
        if item.isupper():
            if item in self.dict:
                return self.dict[item]

            return self.env.get(item, None)

        if item == 'e':
            from utils import e
            return e

        if item == 'sh':
            from utils import sh_str
            return sh_str

        if item == 'int':
            return int

        if item == 'str':
            return str

        if item == 'include':
            return self.include

        if item in self.dict:
            return self.dict[item]

        arr = ConfigArray()
        self.dict[item] = arr
        return arr

    def __setitem__(self, key, value):
        if key.isupper():
            self.env[key] = value
        else:
            self.dict[key] = value

    def include(self, filename):
        filename = os.path.expandvars(filename)
        if filename[0] != '/':
            filename = os.path.join(os.path.dirname(self.filename), filename)

        d = load_file(filename, self.env)
        for k, v in d.items():
            if k in self.dict:
                if isinstance(self.dict[k], dict):
                    self.dict[k].update(v)
                elif isinstance(self.dict[k], list):
                    self.dict[k] += v
            else:
                self.dict[k] = v


def load_file(filename, env):
    g = GlobalsWrapper(env, filename)
    execfile(os.path.expandvars(filename), g)
    return g.dict

def load_profile_config():
    return load_file('${BUILD_PROFILES}/${PROFILE}/config.pyd', os.environ)
