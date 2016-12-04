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

import argparse
import socket
import threading
import serial


class Main(object):
    def __init__(self):
        self.console = None
        self.server = None
        self.logfile = None
        self.clients = []

    def handle_connection(self, sock, addr):
        print('New connection from {0}:{1}'.format(*addr))
        self.clients.append(sock)

        # Disable local echo
        sock.send('\xff\xfb\x01')
        sock.recv(3)

        # Suppress go-ahead
        sock.send('\xff\xfb\x03')
        sock.recv(3)

        while True:
            ch = sock.recv(1)
            if not ch:
                print('Connection from {0}:{1} closed'.format(*addr))
                self.clients.remove(sock)
                sock.shutdown(socket.SHUT_RDWR)
                return

            self.console.write(ch)

    def console_reader(self):
        while True:
            try:
                ch = self.console.read()
            except serial.SerialException as e:
                print('Cannot read from serial port: {0}'.format(str(e)))
                return

            if self.logfile:
                self.logfile.write(ch)
                if ch == '\n':
                    self.logfile.flush()

            for i in self.clients:
                i.send(ch)

    def start_server(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        sock.bind(('', port))
        sock.listen(1)

        while True:
            try:
                client, addr = sock.accept()
            except KeyboardInterrupt:
                sock.shutdown(socket.SHUT_RDWR)
                return

            t = threading.Thread(target=self.handle_connection, args=(client, addr))
            t.daemon = True
            t.start()

    def main(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', metavar='CON-PORT', help='Port device node')
        parser.add_argument('-l', metavar='LOGFILE', help='Log file')
        parser.add_argument('-p', metavar='TCP-PORT', help='TCP port number to listen on')

        args = parser.parse_args()

        if args.l:
            self.logfile = open(args.l, 'a+')

        try:
            self.console = serial.Serial(args.c, 9600)
        except OSError as e:
            print('Cannot open serial port: {0}'.format(str(e)))
            return

        t1 = threading.Thread(target=self.console_reader)
        t1.daemon = True
        t1.start()

        self.start_server(int(args.p))

        if self.logfile:
            self.logfile.close()

        self.console.close()


if __name__ == '__main__':
    m = Main()
    m.main()
