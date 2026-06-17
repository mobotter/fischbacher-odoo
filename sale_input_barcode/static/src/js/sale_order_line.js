/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SaleOrderLineProductField } from "@sale/js/sale_product_field";

console.log("[sale_input_barcode] component auto-next loaded");

const ADD_PRODUCT_SELECTOR = '.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]';
const PRODUCT_INPUT_SELECTOR = 'td[name="product_template_id"] input.o-autocomplete--input';

function getAddProductLink() {
    const links = Array.from(document.querySelectorAll(ADD_PRODUCT_SELECTOR));
    return links.find((el) => {
        const text = (el.textContent || '').trim();
        return text === 'Produkt hinzufügen' || text === 'Add a product' || text === 'Produkt hinzufügen';
    }) || null;
}

function focusNewestProductInput(retries = 8) {
    const tryFocus = () => {
        const inputs = document.querySelectorAll(PRODUCT_INPUT_SELECTOR);
        if (inputs.length) {
            const input = inputs[inputs.length - 1];
            input.focus();
            input.click();
            return;
        }
        if (retries > 0) {
            window.setTimeout(() => focusNewestProductInput(retries - 1), 150);
        }
    };
    window.setTimeout(tryFocus, 180);
}

function addNextProductLine() {
    const addLink = getAddProductLink();
    if (!addLink) {
        console.log('[sale_input_barcode] add link not found');
        return;
    }
    console.log('[sale_input_barcode] clicking add product link after selection');
    addLink.click();
    focusNewestProductInput();
}

patch(SaleOrderLineProductField.prototype, {
    async updateRecord(value, params = {}) {
        const result = await super.updateRecord(value, params);
        const selectedId = Array.isArray(value) ? value[0] : value;
        if (!selectedId) {
            return result;
        }
        window.setTimeout(() => {
            addNextProductLine();
        }, 250);
        return result;
    },
});
