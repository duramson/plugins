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

    Deutsche Telekom Glasfaser-Modem 2 and 2b.

    The modem serves its data below /ONT/client/data/ as lists of
    {"vartype", "varid", "varvalue"} entries, all values as strings.
    Without an Accept-Language header it answers with an invalid status line,
    so the header is mandatory.

    Status.json holds the measurements, FirmwareUpdate.json the firmware date
    and the automatic update setting. A GET on Reboot.json only reads the last
    restart, a POST with reboot_device=true restarts the modem (as the restart
    button of its web interface does). The ploam_* values belong to the PLOAM
    password, not to the PON state, which the modem does not report.
"""

import http.client
import json
import urllib.parse
import urllib.request

from .errors import OntError

STATUS_PATH = '/ONT/client/data/Status.json'
FIRMWARE_PATH = '/ONT/client/data/FirmwareUpdate.json'
REBOOT_PATH = '/ONT/client/data/Reboot.json'


def _number(value, kind=float):
    """Modem values are strings; '--' or '' mean "no value" (e.g. laser off)."""
    try:
        return kind(value)
    except (TypeError, ValueError):
        return None


def _serial(value):
    """PON serial number: 4 ASCII vendor characters + 8 hex digits, sent hex encoded."""
    if not value or len(value) != 16:
        return value or None
    try:
        vendor = bytes.fromhex(value[:8]).decode('ascii')
    except ValueError:
        return value
    return vendor + value[8:].upper() if vendor.isprintable() else value


def _serial_hex(value):
    """The same serial in its 16 digit form, as some providers ask for it."""
    try:
        bytes.fromhex(value)
    except (TypeError, ValueError):
        return None
    return value.upper() if len(value) == 16 else None


def _values(entries):
    return {e.get('varid'): e.get('varvalue') for e in entries
            if isinstance(e, dict) and e.get('vartype') == 'value'}


def _flag(value):
    return {'1': True, '0': False}.get(value)


def parse(entries, firmware_entries=()):
    """Turn the Status.json (and FirmwareUpdate.json) lists into the normalized driver result."""
    raw = _values(firmware_entries)
    raw.update(_values(entries))
    return {
        'device': {
            'model': raw.get('device_name') or None,
            'hardware': raw.get('hardware_revision') or None,
            'firmware': raw.get('firmware_version') or None,
            'firmware_standby': raw.get('fw_version_standby') or None,
            'firmware_date': raw.get('firmware_date') or None,
            'auto_update': _flag(raw.get('autofw_active')),
            'serial': _serial(raw.get('serial_number')),
            'serial_hex': _serial_hex(raw.get('serial_number')),
        },
        'optical': {
            'rx_power_dbm': _number(raw.get('rxpower')),
            'tx_power_dbm': _number(raw.get('txpower')),
        },
        'pon': {
            'bip_errors': _number(raw.get('rxbip_crc'), int),
        },
        'lan': {
            'link_mbps': _number(raw.get('link_status'), int),
            'link_seconds': _number(raw.get('stability'), int),
            'rx_bytes': _number(raw.get('rxbytes'), int),
            'tx_bytes': _number(raw.get('txbytes'), int),
            'rx_packets': _number(raw.get('rxpackets'), int),
            'tx_packets': _number(raw.get('txpackets'), int),
            'rx_dropped': _number(raw.get('rxdrop_packets'), int),
        },
        'raw': raw,
    }


def _request(address, path, timeout, data=None):
    request = urllib.request.Request(
        'http://%s%s' % (address, path),
        data=None if data is None else urllib.parse.urlencode(data).encode(),
        headers={'Accept-Language': 'en'}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            entries = json.load(response)
    except OSError as e:  # includes URLError, HTTPError and timeouts
        raise OntError('ONT not reachable at %s: %s' % (address, getattr(e, 'reason', e)))
    except ValueError:
        raise OntError('ONT at %s sent no valid status data' % address)
    if not isinstance(entries, list):
        raise OntError('ONT at %s sent unexpected status data' % address)
    return entries


def fetch(address, timeout):
    entries = _request(address, STATUS_PATH, timeout)
    try:
        firmware_entries = _request(address, FIRMWARE_PATH, timeout)
    except OntError:
        # firmware details are optional, the status alone is still useful
        firmware_entries = ()
    return parse(entries, firmware_entries)


def restart(address, timeout):
    try:
        _request(address, REBOOT_PATH, timeout, {'reboot_device': 'true'})
    except OntError as e:
        # the modem accepts the request and drops the connection without an answer
        if not isinstance(e.__context__, http.client.RemoteDisconnected):
            raise
