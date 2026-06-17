/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

const PRODUCT_CELL_SELECTOR = 'td[name="product_template_id"]';
const PRODUCT_INPUT_SELECTOR = 'td[name="product_template_id"] input.o-autocomplete--input';
const ORDER_LINE_TABLE_SELECTOR = '.o_sale_input_barcode_order_line';

function inSaleOrderLineProductCell(component) {
    const root = component?.el;
    if (!root) {
        return false;
    }
    return !!root.closest(PRODUCT_CELL_SELECTOR) && !!document.querySelector(ORDER_LINE_TABLE_SELECTOR);
}

function focusNewestProductInput() {
    window.setTimeout(() => {
        const table = document.querySelector(ORDER_LINE_TABLE_SELECTOR);
        if (!table) {
            return;
        }
        const inputs = table.querySelectorAll(PRODUCT_INPUT_SELECTOR);
        if (!inputs.length) {
            return;
        }
        const input = inputs[inputs.length - 1];
        input.focus();
        input.click();
    }, 250);
}

function clickAddProduct() {
    const table = document.querySelector(ORDER_LINE_TABLE_SELECTOR);
    if (!table) {
        return;
    }
    const candidates = Array.from(document.querySelectorAll('a, button, div[role="button"]'));
    const addButton = candidates.find((el) => {
        const text = (el.textContent || '').trim();
        return text === 'Add a product' || text === 'Produkt hinzuf├╝gen' || text === 'Add a line';
    });
    if (!addButton) {
        return;
    }
    addButton.click();
    focusNewestProductInput();
}

patch(Many2OneField.prototype, {
    async update(value, params = {}) {
        const result = await super.update(value, params);
        if (!inSaleOrderLineProductCell(this)) {
            return result;
        }
        if (!value) {
            return result;
        }
        window.setTimeout(() => {
            clickAddProduct();
        }, 150);
        return result;
    },
});
