/** @odoo-module **/

import { registry } from "@web/core/registry";
import { many2OneField, Many2OneField } from "@web/views/fields/many2one/many2one_field";

export class QuotationLineProductField extends Many2OneField {
    static template = "ol_sale_subscription_extensions.QuotationLineProductField";

    onDescriptionInput(ev) {
        this.props.record.update({
            name: ev.target.value,
        });
    }
}

export const quotationLineProductField = {
    ...many2OneField,
    component: QuotationLineProductField,
};

registry.category("fields").add("quotation_line_product", quotationLineProductField);
