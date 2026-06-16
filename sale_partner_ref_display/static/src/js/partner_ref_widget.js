/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

if (Many2OneField && Many2OneField.prototype) {
    patch(Many2OneField.prototype, {
        setup() {
            super.setup(...arguments);
            const { record, name } = this.props;
            if (
                name === "partner_id" &&
                record &&
                record.resModel === "sale.order"
            ) {
                const originalGetContext = this.getContext?.bind(this);
                if (originalGetContext) {
                    this.getContext = () => ({
                        ...originalGetContext(),
                        show_ref_prefix: true,
                    });
                }
            }
        },
    });
}
