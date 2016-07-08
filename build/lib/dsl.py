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
import ast
import json
DSL_PREFIX = 'dsl.config.'


class ConfigDict(dict):
    def __getattr__(self, item):
        return self.get(item)


class ConfigArray(list):
    def __iadd__(self, other):
        if type(other) not in (list, ConfigArray):
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
        self.dict = ConfigDict()
        self.filename = filename
        self.env = env

    def __getitem__(self, item):
        if item.isupper():
            if item in self.dict:
                return self.dict[item]

            return self.env.get(item, None)

        if item == 'ConfigDict':
            return ConfigDict

        if item == 'ConfigArray':
            return ConfigArray

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

        if item == 'exists':
            return os.path.exists

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


class AstTransformer(ast.NodeTransformer):
    def visit_Str(self, node):
        return ast.Call(
            func=ast.Name(id='e', ctx=ast.Load()),
            args=[node],
            keywords=[],
            starargs=None,
            kwargs=None
        )

    def visit_List(self, node):
        self.generic_visit(node)
        return ast.Call(
            func=ast.Name(id='ConfigArray', ctx=ast.Load()),
            args=[node],
            keywords=[],
            starargs=None,
            kwargs=None
        )

    def visit_Dict(self, node):
        self.generic_visit(node)
        return ast.Call(
            func=ast.Name(id='ConfigDict', ctx=ast.Load()),
            args=[node],
            keywords=[],
            starargs=None,
            kwargs=None
        )


def load_file(filename, env):
    from utils import e
    filename = e(filename)
    g = GlobalsWrapper(env, filename)
    with open(filename, 'r') as f:
        tree = ast.parse(f.read(), filename)
        t2 = ast.fix_missing_locations(AstTransformer().visit(tree))
        exec(compile(t2, filename, 'exec'), g)

    return g.dict


def override_profile_config(config):
    # local import may be needed to avoid circular import issues
    from utils import info
    override = {k.replace(DSL_PREFIX, ''): v for k, v in os.environ.items() if k.startswith(DSL_PREFIX)}
    for k, v in override.items():
        dest = None
        split_keys = k.split('.')
        try:
            for subkey in split_keys[:-1]:
                dest = dest or config
                if isinstance(dest, dict):
                    dest = dest[subkey]
                elif isinstance(dest, list):
                    for dictitem in dest:
                        if dictitem['name'] == subkey:
                            dest = dictitem
                            break
                    else:
                        raise KeyError(subkey)
            if dest and isinstance(dest, dict):
                dest[split_keys[-1]] = v
            else:
                # means that the split resulted in a single element
                # thus we can just use the original key
                config[k] = v
            info('Overriding {0}{1} build config var to: {2}'.format(DSL_PREFIX, k, v))
        except KeyError as e:
            # this key does not exist in the build config
            # moving on post logging this
            info('{0}{1} is not a proper build config key! KeyError for {2}'.format(DSL_PREFIX, k, e))
    return config


def load_profile_config():
    return override_profile_config(load_file(
        '${BUILD_PROFILES}/${PROFILE}/config.pyd', os.environ
    ))
