#!/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2020 h-mineta <h-mineta@nt.ctc.co.jp>
# This software is released under the MIT License.

import argparse
import ipaddress
import os
import re
import sys
import urllib.request, urllib.parse, urllib.error

parser = argparse.ArgumentParser(description='Generate .htaccess to block for Tor')

parser.add_argument('--torbulkexitlist',
                    action='store',
                    nargs=1,
                    default='https://check.torproject.org/cgi-bin/TorBulkExitList.py',
                    type=str,
                    help='TorBulkExitList')

parser.add_argument('-p', '--port',
                    action='store',
                    nargs='?',
                    default=80,
                    type=int,
                    help='destination TCP/UDP port number')

parser.add_argument('-e', '--export-dir',
                    action='store',
                    nargs='?',
                    default='.',
                    type=str,
                    help='directory to export .htaccess')

parser.add_argument('--http-proxy',
                    action='store',
                    nargs='?',
                    const=None,
                    default=None,
                    type=str,
                    choices=None,
                    help='HTTP Proxy(default: None)',
                    metavar=None)

parser.add_argument('address',
                    action='store',
                    nargs=1,
                    const=None,
                    default=None,
                    type=str,
                    choices=None,
                    help='Destination address',
                    metavar=None)

args = parser.parse_args()

def main(args):
    try:
        destination_ipv4address = ipaddress.ip_address(args.address[0])
    except ValueError:
        print('[error] Destination address is invalid ({})'.format(args.address[0]), file=sys.stderr)
        exit(1)

    request_params = {
        'ip': str(destination_ipv4address),
        'port': args.port,
    }

    opener = urllib.request.build_opener()

    # Proxy有り
    if args.http_proxy:
        proxy_handler = urllib.request.ProxyHandler({
            "http": args.http_proxy,
            "https": args.http_proxy
        })
        opener.add_handler(proxy_handler)

    request = urllib.request.Request('{}?{}'.format(args.torbulkexitlist, urllib.parse.urlencode(request_params)))
    try:
        with opener.open(request) as request:
            response = request.read().decode('utf-8')
    except urllib.error.HTTPError as ex:
        print('[error] HTTP access error code:{}'.format(ex.code), file=sys.stderr)
        exit(2)
    except urllib.error.URLError as ex:
        print('[error] HTTP access error', file=sys.stderr)
        print('[error] {}'.format(ex.reason), file=sys.stderr)
        exit(2)


    exit_list_strings = []

    for line in response.split('\n'):
        if re.match(r'^#', line):
            # コメント行はskip
            continue
        elif re.match(r'^$', line):
            # データなしもスキップ
            continue

        # IPv4 address format確認
        try:
            ipaddress.ip_address(line)
        except ValueError:
            print('[error] address is invalid({})'.format(line), file=sys.stderr)
            continue
        except Exception as ex:
            print('[error] ', end='', file=sys.stderr)
            print(ex, file=sys.stderr)
            continue

        # 拒否リスト生成
        exit_list_strings.append('    Require not ip {}\n'.format(line))

    print('[info] Tor exit list count : {:d}'.format(len(exit_list_strings)))

    try:
        # 指定ディレクトリ配下に.htaccess書き込み
        with  open('{}/.htaccess'.format(args.export_dir), 'w') as file_htaccess:
            file_htaccess.write('<RequireAll>\n')
            file_htaccess.write('    Require all granted\n')
            file_htaccess.writelines(exit_list_strings)
            file_htaccess.write('</RequireAll>\n')
            file_htaccess.flush()

    except Exception as ex:
        print('[error] ', end='', file=sys.stderr)
        print(ex, file=sys.stderr)
        exit(3)

if __name__ == '__main__':
    main(args)
