/** @odoo-module **/

const PRODUCT_INPUT_SELECTOR = 'td[name="product_template_id"] input.o-autocomplete--input';
const ORDER_LINE_TABLE_SELECTOR = '.o_sale_input_barcode_order_line';

function isSaleOrderProductInput(el) {
    return el && el.matches && el.matches(PRODUCT_INPUT_SELECTOR);
}

function focusNextProductInput() {
    window.setTimeout(() => {
        const table = document.querySelector(ORDER_LINE_TABLE_SELECTOR);
        if (!table) {
            return;
        }
        const inputs = table.querySelectorAll(PRODUCT_INPUT_SELECTOR);
        if (!inputs.length) {
            return;
        }
        const last = inputs[inputs.length - 1];
        last.focus();
        last.click();
    }, 250);
}

function triggerAddLine() {
    const addButtons = Array.from(document.querySelectorAll('a, button, div[role="button"]')).filter((el) => {
        const text = (el.textContent || '').trim();
        return text === 'Add a product' || text === 'Produkt hinzuf├╝gen' || text === 'Zeile hinzuf├╝gen';
    });
    if (addButtons.length) {
        addButtons[0].click();
        focusNextProductInput();
    }
}

document.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Enter') {
        return;
    }
    if (!isSaleOrderProductInput(ev.target)) {
        return;
    }
    window.setTimeout(() => {
        triggerAddLine();
    }, 150);
}, true);
