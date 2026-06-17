/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

console.log("[sale_input_barcode] asset loaded");

const PRODUCT_CELL_SELECTOR = 'td[name="product_template_id"]';
const PRODUCT_INPUT_SELECTOR = 'td[name="product_template_id"] input.o-autocomplete--input';
const ORDER_LINE_TABLE_SELECTOR = '.o_sale_input_barcode_order_line';

function inSaleOrderLineProductCell(component) {
    const root = component?.el;
    const inCell = !!root && !!root.closest(PRODUCT_CELL_SELECTOR) && !!document.querySelector(ORDER_LINE_TABLE_SELECTOR);
    console.log("[sale_input_barcode] inSaleOrderLineProductCell", {
        hasRoot: !!root,
        inCell,
        root,
    });
    return inCell;
}

function focusNewestProductInput() {
    console.log("[sale_input_barcode] focusNewestProductInput start");
    window.setTimeout(() => {
        const table = document.querySelector(ORDER_LINE_TABLE_SELECTOR);
        if (!table) {
            console.log("[sale_input_barcode] no order line table found for focus");
            return;
        }
        const inputs = table.querySelectorAll(PRODUCT_INPUT_SELECTOR);
        console.log("[sale_input_barcode] product inputs found", inputs.length);
        if (!inputs.length) {
            return;
        }
        const input = inputs[inputs.length - 1];
        console.log("[sale_input_barcode] focusing newest input", input);
        input.focus();
        input.click();
    }, 250);
}

function clickAddProduct() {
    console.log("[sale_input_barcode] clickAddProduct start");
    const table = document.querySelector(ORDER_LINE_TABLE_SELECTOR);
    if (!table) {
        console.log("[sale_input_barcode] no order line table found for add button");
        return;
    }
    const candidates = Array.from(document.querySelectorAll('a, button, div[role="button"]'));
    console.log("[sale_input_barcode] clickable candidates", candidates.length);
    const addButton = candidates.find((el) => {
        const text = (el.textContent || '').trim();
        return text === 'Add a product' || text === 'Produkt hinzufügen' || text === 'Add a line';
    });
    if (!addButton) {
        console.log("[sale_input_barcode] add button not found");
        return;
    }
    console.log("[sale_input_barcode] add button found", addButton);
    addButton.click();
    focusNewestProductInput();
}

patch(Many2OneField.prototype, {
    async update(value, params = {}) {
        console.log("[sale_input_barcode] Many2OneField.update called", { value, params, component: this });
        const result = await super.update(value, params);
        console.log("[sale_input_barcode] Many2OneField.update after super", { value, result, component: this });
        if (!inSaleOrderLineProductCell(this)) {
            console.log("[sale_input_barcode] skipped: not in sale order product cell");
            return result;
        }
        if (!value) {
            console.log("[sale_input_barcode] skipped: empty value");
            return result;
        }
        window.setTimeout(() => {
            console.log("[sale_input_barcode] trying clickAddProduct after selection");
            clickAddProduct();
        }, 150);
        return result;
    },
});
