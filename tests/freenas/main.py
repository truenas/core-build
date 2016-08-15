#+
# Copyright 2016 iXsystems, Inc.
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

import os
import json
import time
import argparse
import shutil
import subprocess
from utils import e, sh, objdir, info
from xml.etree.ElementTree import Element, SubElement, tostring, parse
from distutils.core import run_setup
from xml.dom import minidom


PYTHON_DEPS = [
    'Cython',
    'paramiko',
    'nose2',
    e('${BE_ROOT}/py-freenas.utils'),
    e('${BE_ROOT}/dispatcher-client/python')
]


EXCLUDES = ['os', 'objs', 'ports', 'release', 'release.build.log', 'repo-manifest']


venv_root = objdir('test-venv')
output_root = objdir('test-output')


class Main(object):
    def __init__(self):
        self.address = None
        self.username = None
        self.password = None
        self.test_suites = []
        self.output_path = None
        self.excluded = ['os', 'objs', 'ports', 'release']

    def find_tests(self):
        info('Looking for test manifests in ${{BE_ROOT}}')
        for dir in os.listdir(e('${BE_ROOT}')):
            if dir not in self.excluded:
                for root, _, files in os.walk(os.path.join(e('${BE_ROOT}'), dir)):
                    if os.path.split(root)[1] == 'tests' and 'MANIFEST.json' in files:
                        info('Found test manifest at {0}', root)
                        self.test_suites.append(root)

    def load_manifest(self, path):
        with open(os.path.join(path, 'MANIFEST.json'), 'r') as manifest_file:
            return json.load(manifest_file)

    def run(self):
        for s in self.test_suites:
            start_time = time.time()
            manifest = self.load_manifest(s)
            os.chdir(s)
            args = [e('${venv_root}/bin/python3.4'), os.path.join(s, 'run.py')]
            test = None
            if manifest['pass_target']:
                args.extend([
                    '-a', self.address,
                    '-u', self.username,
                    '-p', self.password,
                    '-x'
                ])
            try:
                test = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    close_fds=True
                )
                test.wait(timeout=manifest['timeout'])
            except subprocess.TimeoutExpired as err:
                self.generate_suite_error(
                    os.path.join(s, 'results.xml'),
                    manifest['name'],
                    time.time() - start_time,
                    'Test timeout reached',
                    err
                )
            except subprocess.SubprocessError as err:
                self.generate_suite_error(
                    os.path.join(s, 'results.xml'),
                    manifest['name'],
                    time.time() - start_time,
                    'Test could not be started',
                    err
                )
            if test and test.returncode:
                self.generate_suite_error(
                    os.path.join(s, 'results.xml'),
                    manifest['name'],
                    time.time() - start_time,
                    'Test process has returned an error',
                    test.stdout.read() + test.stderr.read()
                )

    def aggregate_results(self):
        sh('mkdir -p ${output_root}')
        for s in self.test_suites:
            manifest = self.load_manifest(s)
            try:
                shutil.move(
                    os.path.join(s, 'results.xml'),
                    os.path.join(output_root, '{}-results.xml'.format(manifest['name']))
                )
            except FileNotFoundError as e:
                self.generate_suite_error(
                    os.path.join(output_root, '{}-results.xml'.format(manifest['name'])),
                    manifest['name'],
                    0,
                    'Results file not found',
                    e
                )

        results = Element('testsuites')
        for r in os.listdir(output_root):
            if r.endswith('results.xml'):
                single_result = parse(os.path.join(output_root, r))
                results.append(single_result.getroot())

        with open(os.path.join(output_root, 'aggregated_results.xml'), 'w') as output_file:
            output_file.write(self.print_xml(results))

    def generate_suite_error(self, out_path, name, test_time, text, err):
        top = Element('testsuite', errors="1", failures="0", name=name, skipped="0", tests='0', time=str(test_time))
        case = SubElement(top, 'testcase', classname="UNDEFINED", name="UNDEFINED", time=str(test_time))
        error = SubElement(case, 'error', message=text)
        error.text = str(err)
        SubElement(case, 'system-err')
        with open(out_path, 'w') as output_file:
            output_file.write(self.print_xml(top))

    def print_xml(self, elem):
        rough_string = tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def build_virtualenv(self):
        info('Preparing test runtime environment')
        sh('virtualenv ${venv_root}')
        for i in PYTHON_DEPS:
            sh('${venv_root}/bin/pip install ${i}')

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', metavar='ADDRESS', required=True, help='FreeNAS box address')
        parser.add_argument('-u', metavar='USERNAME', required=True, help='Username')
        parser.add_argument('-p', metavar='PASSWORD', required=True, help='Password')
        args = parser.parse_args()

        self.address = args.a
        self.username = args.u
        self.password = args.p

        self.build_virtualenv()

        self.find_tests()

        self.run()

        self.aggregate_results()


if __name__ == '__main__':
    m = Main()
    m.main()
