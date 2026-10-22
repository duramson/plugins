{#
 * Copyright (C) 2026 Cedrik Theesen
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
 * AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 * OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 #}

<script>
    const rows = [
        ['device', 'model', '{{ lang._('Model') }}'],
        ['device', 'hardware', '{{ lang._('Hardware revision') }}'],
        ['device', 'firmware', '{{ lang._('Firmware') }}'],
        ['device', 'firmware_standby', '{{ lang._('Firmware (standby)') }}'],
        ['device', 'firmware_date', '{{ lang._('Firmware date') }}'],
        ['device', 'auto_update', '{{ lang._('Automatic firmware updates') }}', yesNo],
        ['device', 'serial', '{{ lang._('PON serial number') }}', groups],
        ['device', 'serial_hex', '{{ lang._('PON serial number (hex)') }}', groups],
        ['optical', 'rx_power_dbm', '{{ lang._('Receive power (dBm)') }}'],
        ['optical', 'tx_power_dbm', '{{ lang._('Transmit power (dBm)') }}'],
        ['pon', 'bip_errors', '{{ lang._('BIP errors') }}'],
        ['lan', 'link_mbps', '{{ lang._('LAN link (Mbit/s)') }}'],
        ['lan', 'link_seconds', '{{ lang._('LAN link up for') }}', duration],
        // counters as seen by the ONT: "sent" is what the ONT sent to the firewall
        ['lan', 'rx_bytes', '{{ lang._('Received by the ONT') }}', bytes],
        ['lan', 'tx_bytes', '{{ lang._('Sent by the ONT') }}', bytes],
        ['lan', 'rx_dropped', '{{ lang._('Dropped by the ONT (packets)') }}'],
    ];

    function bytes(value) {
        return byteFormat(value, 2);
    }

    function yesNo(value) {
        return value ? '{{ lang._('enabled') }}' : '{{ lang._('disabled') }}';
    }

    function duration(seconds) {
        const d = Math.floor(seconds / 86400);
        const h = Math.floor(seconds % 86400 / 3600);
        const m = Math.floor(seconds % 3600 / 60);
        return (d ? d + 'd ' : '') + h + 'h ' + m + 'm';
    }

    // blocks of four, as printed on the device label
    function groups(value) {
        return String(value).match(/.{1,4}/g).join(' ');
    }

    function cell(value, format) {
        // values come from the ONT, only ever set them as text
        if (value === null || value === undefined) {
            return $('<td/>').text('{{ lang._('no value') }}');
        }
        return $('<td/>').text(format ? format(value) : value);
    }

    function updateStatus() {
        ajaxGet('/api/ont/status/get', {}, function (data) {
            const $body = $('#ont-status tbody').empty();
            const $raw = $('#ont-raw tbody').empty();
            $('#ont-message').addClass('hidden');
            $('#restartBox').toggleClass('hidden', !data.restart_allowed);
            if (data.status !== 'ok') {
                const text = data.status === 'disabled'
                    ? '{{ lang._('ONT status is disabled, enable it under Settings.') }}'
                    : data.error;
                $('#ont-message').removeClass('hidden').text(text);
                return;
            }
            rows.forEach(function ([section, key, label, format]) {
                $body.append($('<tr/>').append($('<td/>').text(label), cell(data[section][key], format)));
            });
            $('#ont-updated').text(new Date(data.time * 1000).toLocaleTimeString());
            Object.entries(data.raw).forEach(function ([key, value]) {
                $raw.append($('<tr/>').append($('<td/>').text(key), cell(value)));
            });
        });
    }

    $(document).ready(function () {
        mapDataToFormUI({'frm_general_settings': '/api/ont/settings/get'}).done(function () {
            $('.selectpicker').selectpicker('refresh');
        });
        $('#saveAct').click(function () {
            saveFormToEndpoint('/api/ont/settings/set', 'frm_general_settings', updateStatus);
        });
        $('#restartAct').click(function () {
            stdDialogConfirm(
                '{{ lang._('Restart ONT') }}',
                '{{ lang._('The internet connection is down until the ONT has restarted, usually two to three minutes. Restart now?') }}',
                '{{ lang._('Restart') }}',
                '{{ lang._('Cancel') }}',
                function () {
                    ajaxCall('/api/ont/service/restart', {}, function (data) {
                        const ok = data.status === 'ok';
                        $('#ont-message').removeClass('hidden').text(ok
                            ? '{{ lang._('The ONT is restarting.') }}'
                            : (data.error || '{{ lang._('The ONT could not be restarted.') }}'));
                    });
                },
                'warning'
            );
        });
        updateStatus();
        setInterval(updateStatus, 10000);
    });
</script>

<ul class="nav nav-tabs" data-tabs="tabs" id="maintabs">
    <li class="active"><a data-toggle="tab" href="#status">{{ lang._('Status') }}</a></li>
    <li><a data-toggle="tab" href="#raw">{{ lang._('Device values') }}</a></li>
    <li><a data-toggle="tab" href="#settings">{{ lang._('Settings') }}</a></li>
</ul>

<div class="tab-content content-box">
    <div id="status" class="tab-pane fade in active">
        <div class="alert alert-warning hidden" role="alert" id="ont-message" style="margin: 10px;"></div>
        <table class="table table-striped" id="ont-status">
            <tbody></tbody>
        </table>
        <p class="text-muted" style="padding: 0 10px 10px;">
            {{ lang._('Last update') }}: <span id="ont-updated">-</span>
        </p>
        <div class="col-md-12 hidden" id="restartBox" style="padding-bottom: 1.5em;">
            <button class="btn btn-warning" id="restartAct" type="button">{{ lang._('Restart ONT') }}</button>
        </div>
    </div>
    <div id="raw" class="tab-pane fade in">
        <table class="table table-striped table-condensed" id="ont-raw">
            <tbody></tbody>
        </table>
    </div>
    <div id="settings" class="tab-pane fade in">
        {{ partial("layout_partials/base_form", ['fields': generalForm, 'id': 'frm_general_settings']) }}
        <div class="col-md-12" style="padding-bottom: 1.5em;">
            <hr/>
            <button class="btn btn-primary" id="saveAct" type="button"><b>{{ lang._('Save') }}</b></button>
        </div>
    </div>
</div>
