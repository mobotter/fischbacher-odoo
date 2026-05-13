/** @odoo-module **/

import { registry } from "@web/core/registry";
import { SaleOrderLineProductField } from "@sale/js/sale_product_field";

export class QuotationLineProductField extends SaleOrderLineProductField {
    get isQuotationLine() {
        return this.props.record.resModel === "sale.quotation.line";
    }
}

registry.category("fields").add("quotation_line_product", {
    ...registry.category("fields").get("sol_product_many2one"),
    component: QuotationLineProductField,
});
