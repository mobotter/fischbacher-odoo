/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { useDebounced } from "@web/core/utils/timing";

export class QuotationLineProductField extends Component {
    static template = "ol_sale_subscription_extensions.QuotationLineProductField";
    static components = { Many2OneField };
    static props = {
        ...standardFieldProps,
    };
    static supportedTypes = ["many2one"];

    setup() {
        this.state = useState({
            showDescription: false,
        });
        this.debouncedUpdate = useDebounced((value) => {
            this.props.record.update({ name: value });
        }, 300);
    }

    get description() {
        return this.props.record.data.name || "";
    }

    get isSectionOrNote() {
        return !!this.props.record.data.display_type;
    }

    toggleDescription() {
        this.state.showDescription = !this.state.showDescription;
    }

    onDescriptionInput(ev) {
        this.debouncedUpdate(ev.target.value);
    }

    get many2OneProps() {
        return {
            ...this.props,
            canOpen: true,
        };
    }
}

registry.category("fields").add("quotation_line_product", {
    component: QuotationLineProductField,
    supportedTypes: ["many2one"],
});
