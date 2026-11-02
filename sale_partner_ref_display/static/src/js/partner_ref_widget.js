/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

console.log("=== sale_partner_ref_display: JS loaded ===");

patch(Many2OneField.prototype, {
    setup() {
        console.log("=== Many2OneField setup() ===");
        console.log("this.props:", this.props);
        
        super.setup(...arguments);
        
        const { record, name } = this.props;
        console.log("name:", name);
        console.log("record.resModel:", record?.resModel);
        
        if (
            name === "partner_id" &&
            record &&
            record.resModel === "sale.order"
        ) {
            console.log("=== MATCH: partner_id on sale.order ===");
            
            // Domain erzwingen
            console.log("Overriding getDomain");
            this.getDomain = () => {
                const domain = [('active', '=', true), ('parent_id', '=', false)];
                console.log("getDomain returning:", domain);
                return domain;
            };
        } else {
            console.log("=== NO MATCH ===");
            console.log("name === 'partner_id':", name === "partner_id");
            console.log("record:", !!record);
            console.log("record.resModel === 'sale.order':", record?.resModel === "sale.order");
        }
    },
});

console.log("=== Patch applied ===");
