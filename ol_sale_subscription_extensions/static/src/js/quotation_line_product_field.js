/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field";
import { Component } from "@odoo/owl";
import { useRef } from "@odoo/owl";

export class QuotationLineProductField extends Many2OneField {
    static template = "ol_sale_subscription_extensions.QuotationLineProductField";

    get isConfigurableProduct() {
        return this.props.record.data.is_configurable_product;
    }

    get displayProductType() {
        return this.props.record.data.product_type;
    }
}

export const quotationLineProductField = {
    ...many2OneField,
    component: QuotationLineProductField,
};

registry.category("fields").add("quotation_line_product", quotationLineProductField);
