/*
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
 */

export default class Ont extends BaseTableWidget {
    constructor() {
        super();
        this.tickTimeout = 30;
    }

    getMarkup() {
        const $container = $('<div></div>');
        $container.append(this.createTable('ont-table', {headerPosition: 'left'}));
        return $container;
    }

    async onWidgetTick() {
        const data = await this.ajaxCall('/api/ont/status/get');

        if (data.status === 'disabled') {
            this.displayMessage(this.translations.disabled, 'text-muted');
            return;
        }
        if (data.status !== 'ok') {
            this.displayMessage(data.error, 'text-danger');
            return;
        }

        const t = this.translations;
        super.updateTable('ont-table', [
            [t.model, this.text(data.device.model)],
            [t.serial, this.text(this.groups(data.device.serial))],
            [t.rx_power, this.text(this.dbm(data.optical.rx_power_dbm))],
            [t.tx_power, this.text(this.dbm(data.optical.tx_power_dbm))],
            [t.bip_errors, this.text(data.pon.bip_errors)],
            [t.lan_link, this.text(data.lan.link_mbps === null ? null : data.lan.link_mbps + ' Mbit/s')],
        ]);
    }

    dbm(value) {
        return value === null ? null : value.toFixed(2) + ' dBm';
    }

    /* blocks of four, as printed on the device label */
    groups(value) {
        return value === null ? null : value.match(/.{1,4}/g).join(' ');
    }

    /* Values come from the ONT, never insert them as HTML. */
    text(value) {
        const shown = value === null || value === undefined ? this.translations.no_value : String(value);
        return $('<span></span>').text(shown).prop('outerHTML');
    }

    displayMessage(text, cssClass) {
        // a flextable-row is removed by updateTable() on the next successful tick
        const $row = $('<div class="flextable-row" style="justify-content: center"></div>').addClass(cssClass).text(text);
        $('#ont-table').html($row);
    }
}
