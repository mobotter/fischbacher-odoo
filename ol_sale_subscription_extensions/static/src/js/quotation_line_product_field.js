/** @odoo-module **/

import { registry } from "@web/core/registry";
import { many2OneField, Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class QuotationDescriptionDialog extends Component {
    static template = xml`
        <Dialog title="'Produktbeschreibung bearbeiten'">
            <div class="p-3">
                <textarea t-model="props.value"
                          class="form-control"
                          rows="10"
                          t-ref="textarea"/>
            </div>
            <t t-set-slot="footer">
                <button class="btn btn-secondary" t-on-click="props.close">Abbrechen</button>
                <button class="btn btn-primary" t-on-click="() => props.save(props.value)">Speichern</button>
            </t>
        </Dialog>
    `;
    static components = { Dialog };
    static props = ["close", "save", "value"];
}

export class QuotationLineProductField extends Many2OneField {
    static template = "ol_sale_subscription_extensions.QuotationLineProductField";

    setup() {
        super.setup();
        this.dialog = useService("dialog");
    }

    get hasDescriptionButton() {
        return !this.props.record.data.display_type;
    }

    async onClickDescription(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const record = this.props.record;
        const currentValue = record.data.name || "";

        this.dialog.add(QuotationDescriptionDialog, {
            value: currentValue,
            save: async (newValue) => {
                await record.update({ name: newValue });
            },
        });
    }
}

export const quotationLineProductField = {
    ...many2OneField,
    component: QuotationLineProductField,
};

registry.category("fields").add("quotation_line_product", quotationLineProductField);
