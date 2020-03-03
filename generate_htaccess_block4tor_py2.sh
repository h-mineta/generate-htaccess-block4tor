#!/bin/bash
./generate_htaccess_block4tor_py2.py -p 443 -e /var/www/html/ `dig @8.8.8.8 0nyx.net +short`
