/** @odoo-module **/

import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";

class MultilinePartnerNameField extends CharField {
    static template = "contact_custom_fields.MultilinePartnerNameField";

    updateValue(event) {
        this.props.update(event.target.value);
    }
}

registry.category("fields").add("multiline_partner_name", {
    component: MultilinePartnerNameField,
    supportedTypes: ["char"],
});
