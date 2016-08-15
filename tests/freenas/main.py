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
from xml.etree.ElementTree import Element, SubElement, tostring, parse
from xml.dom import minidom


class Main(object):
    def __init__(self):
        self.be_path = None
        self.address = None
        self.username = None
        self.password = None
        self.test_suites = []
        self.output_path = None

    def find_tests(self):
        for root, _, files in os.walk(self.be_path):
            if os.path.split(root)[1] == 'tests' and 'MANIFEST.json' in files:
                self.test_suites.append(root)

    def load_manifest(self, path):
        with open(os.path.join(path, 'MANIFEST.json'), 'r') as manifest_file:
            return json.load(manifest_file)

    def run(self):
        for s in self.test_suites:
            start_time = time.time()
            manifest = self.load_manifest(s)
            args = ['python3.4', os.path.join(s, 'run.py')]
            if manifest['pass_target']:
                args.extend([
                    '-u', self.username,
                    '-p', self.password,
                    '-x', self.output_path,
                    self.address
                ])
            try:
                test = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    close_fds=True
                )
                test.wait(timeout=manifest['timeout'])
            except subprocess.TimeoutExpired as e:
                self.generate_suite_error(
                    os.path.join(s, 'results.xml'),
                    manifest['name'],
                    time.time() - start_time,
                    'Test timeout reached',
                    e
                )
            except subprocess.SubprocessError as e:
                self.generate_suite_error(
                    os.path.join(s, 'results.xml'),
                    manifest['name'],
                    time.time() - start_time,
                    'Test process has returned an error',
                    e
                )

    def aggregate_results(self):
        for s in self.test_suites:
            manifest = self.load_manifest(s)
            try:
                shutil.move(
                    os.path.join(s, 'results.xml'),
                    os.path.join(self.output_path, '{}-results.xml'.format(manifest['name']))
                )
            except FileNotFoundError as e:
                self.generate_suite_error(
                    os.path.join(self.output_path, '{}-results.xml'.format(manifest['name'])),
                    manifest['name'],
                    0,
                    'Results file not found',
                    e
                )

        results = Element('testsuites')
        for r in os.listdir(self.output_path):
            if r.endswith('results.xml'):
                single_result = parse(os.path.join(self.output_path, r))
                results.append(single_result.getroot())

        with open(os.path.join(self.output_path, 'aggregated_results.xml'), 'wb') as output_file:
            output_file.write(self.print_xml(results))

    def generate_suite_error(self, out_path, name, test_time, text, err):
        top = Element('testsuite', errors="1", failures="0", name=name, skipped="0", tests=0, time=test_time)
        case = SubElement(top, 'testcase', classname="UNDEFINED", name="UNDEFINED", time=test_time)
        error = SubElement(case, 'error', message=text)
        error.text = err
        SubElement(case, 'system-err')
        with open(out_path, 'wb') as output_file:
            output_file.write(self.print_xml(top))

    def print_xml(self, elem):
        rough_string = tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', metavar='ADDRESS', required=True, help='FreeNAS box address')
        parser.add_argument('-u', metavar='USERNAME', required=True, help='Username')
        parser.add_argument('-p', metavar='PASSWORD', required=True, help='Password')
        parser.add_argument('-e', metavar='BE', default=os.path.dirname(os.getcwd()), help="Build environment path")
        parser.add_argument('-r', metavar='RESULTS', default=os.path.dirname(os.getcwd()), help="Results path")
        args = parser.parse_args()

        self.be_path = args.e
        self.address = args.a
        self.username = args.u
        self.password = args.p
        self.output_path = args.r

        self.find_tests()

        self.run()

        self.aggregate_results()


if __name__ == '__main__':
    m = Main()
    m.main()
