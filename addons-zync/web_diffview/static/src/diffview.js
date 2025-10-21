/** @odoo-module **/

import { registry } from '@web/core/registry';
import { CharField } from "@web/views/fields/char/char_field";
const { Component, onWillUpdateProps, useRef, onMounted, useState } = owl;

export class DiffView extends CharField {

    setup() {
        super.setup();
        this.iframe = useRef('iframe1');
        onWillUpdateProps((nextProps) => this.putHtmlIntoIFrame(nextProps));
    }
    putHtmlIntoIFrame(nextProps) {
        debugger;
        const val = nextProps.value || "";
        if (!this.iframe) {
            return;
        }
        const $el = this.iframe.el;
        if (!$el) {
            return;
        }
        const doc = $el.contentWindow.document;
        doc.open();
        doc.write(val);
        doc.close();
    }
    get formattedValue() {
        const val = this.props.record._textValues[this.props.name];
        this.putHtmlIntoIFrame({ value: val });
        return val;
    }
}

// DiffView.props = {
//     text: { type: String },
// };
DiffView.template = "diff_view.widget";
registry.category("fields").add("diff_view", {
    component: DiffView,
    supportedTypes: ["char", "text"]
});
