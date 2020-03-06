#!/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (c) 2020 h-mineta <h-mineta@nt.ctc.co.jp>
# This software is released under the MIT License.

from __future__ import with_statement
from __future__ import absolute_import
import argparse
import os
import re
import sys
import urllib2, urllib
from io import open

parser = argparse.ArgumentParser(description='Generate .htaccess to block for Tor')

parser.add_argument('--torbulkexitlist',
                    action='store',
                    nargs=1,
                    default='https://check.torproject.org/cgi-bin/TorBulkExitList.py',
                    type=unicode,
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
                    type=unicode,
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
                    type=unicode,
                    choices=None,
                    help='Destination address',
                    metavar=None)

args = parser.parse_args()

def main(args):
    if (re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', args.address[0])):
        destination_ipv4address = args.address[0]
    else:
        print >>sys.stderr, '[error] Destination address is invalid (%s)' % (args.address[0])
        exit(1)

    request_params = {
        'ip': destination_ipv4address,
        'port': args.port,
    }

    opener = urllib2.build_opener()

    # Proxy有り
    if args.http_proxy:
        proxy_handler = urllib2.ProxyHandler({
            "http": args.http_proxy,
            "https": args.http_proxy
        })
        opener.add_handler(proxy_handler)
    urllib2.install_opener(opener)

    request = urllib2.Request('%s?%s' % (args.torbulkexitlist, urllib.urlencode(request_params)))
    try:
        request = urllib2.urlopen(request)
        response = request.read().decode('utf-8')
    except urllib2.HTTPError, ex:
        print >>sys.stderr, '[error] HTTP access error code:%d' % (ex.code)
        exit(2)
    except urllib2.URLError, ex:
        print >>sys.stderr, '[error] HTTP access error'
        print >>sys.stderr, '[error] %s' % (ex.reason)
        exit(2)


    exit_list_strings = []

    for line in response.split('\n'):
        if re.match(ur'^#', line):
            # コメント行はskip
            continue
        elif re.match(ur'^$', line):
            # データなしもスキップ
            continue

        # IPv4 address format確認
        if (re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', args.address[0])):
            # 拒否リスト生成
            exit_list_strings.append(u'    Require not ip %s\n' % (line))
        else:
            print >>sys.stderr, '[error] address is invalid(%s)' % (line)
            continue

    print '[info] Tor exit list count : %d' % (len(exit_list_strings))

    try:
        # 指定ディレクトリ配下に.htaccess書き込み
        with  open('%s/.htaccess' % (args.export_dir), 'w') as file_htaccess:
            file_htaccess.write(u'<RequireAll>\n')
            file_htaccess.write(u'    Require all granted\n')
            file_htaccess.writelines(exit_list_strings)
            file_htaccess.write(u'</RequireAll>\n')
            file_htaccess.flush()

    except Exception, ex:
        print >>sys.stderr, '[error] ',; sys.stderr.write('')
        print >>sys.stderr, ex
        exit(3)

if __name__ == '__main__':
    main(args)
