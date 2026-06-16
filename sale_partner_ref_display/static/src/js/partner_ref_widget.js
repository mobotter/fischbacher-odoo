/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

/**
 * Patcht das Many2One-Widget für:
 * 1. partner_id im sale.order / subscriptions → show_ref_prefix im Kontext
 * 2. Produktfelder → Quick Create / Create & Edit deaktivieren
 */
patch(Many2OneField.prototype, {
    setup() {
        super.setup(...arguments);

        const { record, name } = this.props;

        // Partner-Dropdown: ref - name
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

        // Produkt-Dropdown in Sales / Subscriptions:
        // Quick Create und Create/Edit clientseitig unterdrücken
        if (
            (name === "product_id" || name === "product_template_id") &&
            record &&
            record.resModel === "sale.order"
        ) {
            this.props.canQuickCreate = false;
            this.props.canCreateEdit = false;

            const originalGetContext = this.getContext?.bind(this);
            if (originalGetContext) {
                this.getContext = () => ({
                    ...originalGetContext(),
                    forbid_quick_create_product: true,
                });
            }
        }
    },
});
