/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class QuotationLineDescriptionField extends Component {
    static template = "ol_sale_subscription_extensions.QuotationLineDescriptionField";
    static props = {
        ...standardFieldProps,
    };
    static supportedTypes = ["text", "char"];

    get value() {
        return this.props.record.data[this.props.name] || "";
    }

    onInput(ev) {
        this.props.record.update({
            [this.props.name]: ev.target.value,
        });
    }
}

registry.category("fields").add("quotation_line_description", {
    component: QuotationLineDescriptionField,
    supportedTypes: ["text", "char"],
});
