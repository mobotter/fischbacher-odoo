/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { useService } from "@web/core/utils/hooks";

/**
 * Patcht das Many2One-Widget für partner_id im sale.order-Formular.
 * Fügt dem RPC-Kontext show_ref_prefix: true hinzu, sodass
 * name_get() die "ref - name"-Darstellung liefert.
 */
patch(Many2OneField.prototype, {
    setup() {
        super.setup(...arguments);
        const { record, name } = this.props;
        // Nur für partner_id in sale.order anwenden
        if (
            name === "partner_id" &&
            record &&
            record.resModel === "sale.order"
        ) {
            // Kontext mit show_ref_prefix erweitern
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
