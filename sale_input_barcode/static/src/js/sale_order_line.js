/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";

console.log("[sale_input_barcode] many2x auto-next loaded");

const ADD_PRODUCT_SELECTOR = '.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]';
const PRODUCT_INPUT_SELECTOR = 'td[name="product_template_id"] input.o-autocomplete--input';

function getAddProductLink() {
    const links = Array.from(document.querySelectorAll(ADD_PRODUCT_SELECTOR));
    return links.find((el) => {
        const text = (el.textContent || "").trim();
        return text === "Produkt hinzufügen" || text === "Add a product";
    }) || null;
}

function focusNewestProductInput(retries = 10) {
    const inputs = document.querySelectorAll(PRODUCT_INPUT_SELECTOR);
    if (inputs.length) {
        const input = inputs[inputs.length - 1];
        console.log("[sale_input_barcode] focus next input", input);
        input.focus();
        input.click();
        return;
    }
    if (retries > 0) {
        window.setTimeout(() => focusNewestProductInput(retries - 1), 150);
    }
}

function addNextProductLine() {
    const addLink = getAddProductLink();
    if (!addLink) {
        console.log("[sale_input_barcode] add link not found");
        return;
    }
    console.log("[sale_input_barcode] clicking add product");
    addLink.click();
    window.setTimeout(() => focusNewestProductInput(), 250);
}

patch(Many2XAutocomplete.prototype, {
    onSelect(option, params = {}) {
        console.log("[sale_input_barcode] onSelect fired", option, params);

        const result = super.onSelect(...arguments);

        const input = this.el?.closest("td")?.querySelector("input.o-autocomplete--input");
        const inProductCell = !!this.el?.closest('td[name="product_template_id"]');

        console.log("[sale_input_barcode] in product cell =", inProductCell);

        if (inProductCell && option) {
            window.setTimeout(() => {
                addNextProductLine();
            }, 300);
        }

        return result;
    },
});
