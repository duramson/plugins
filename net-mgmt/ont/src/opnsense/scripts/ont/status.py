#!/usr/local/bin/python3

"""
    Copyright (C) 2026 Cedrik Theesen
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
    INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
    AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
    AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
    OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
    POSSIBILITY OF SUCH DAMAGE.

    Query the optical network terminal and print its status as JSON.
"""

import argparse
import ipaddress
import json
import time

from drivers import DRIVERS, OntError

parser = argparse.ArgumentParser()
parser.add_argument('driver', choices=DRIVERS.keys())
parser.add_argument('address', type=ipaddress.IPv4Address)
parser.add_argument('--timeout', type=float, default=5)
args = parser.parse_args()

result = {'driver': args.driver, 'address': str(args.address), 'time': int(time.time())}
try:
    result.update(DRIVERS[args.driver].fetch(str(args.address), args.timeout))
    result['status'] = 'ok'
except OntError as e:
    result['status'] = 'error'
    result['error'] = str(e)

print(json.dumps(result))
