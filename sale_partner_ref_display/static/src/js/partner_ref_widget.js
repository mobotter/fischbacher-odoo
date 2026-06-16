/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field";

/**
 * 1) Partner: Kontext show_ref_prefix für sale.order setzen
 * 2) Produkte: Quick Create / Create & Edit im Dropdown deaktivieren
 */

// Instanz-Patch für Kontext am Partnerfeld
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

// Definition-Patch für Many2One-Props
patch(many2OneField, {
    extractProps({ attrs, context, decorations, options, string }, dynamicInfo) {
        const res = super.extractProps({ attrs, context, decorations, options, string }, dynamicInfo);

        const fieldContext = context || {};
        const fieldOptions = options || {};

        const forbidQuickCreate =
            fieldContext.forbid_quick_create_product ||
            fieldOptions.no_quick_create ||
            fieldOptions.no_create ||
            false;

        const forbidCreateEdit =
            fieldContext.forbid_quick_create_product ||
            fieldOptions.no_create_edit ||
            fieldOptions.no_create ||
            false;

        const isProductField =
            res.resModel === "product.product" || res.resModel === "product.template";

        if (isProductField && forbidQuickCreate) {
            res.canQuickCreate = false;
        }

        if (isProductField && forbidCreateEdit) {
            res.canCreateEdit = false;
        }

        return res;
    },
});
