/** @odoo-module **/

console.log("[sale_input_barcode] DOM auto-next loaded");

const ROOT_SELECTOR = '.o_sale_input_barcode_order_line';
const PRODUCT_CELL_SELECTOR = 'td[name="product_template_id"]';
const PRODUCT_INPUT_SELECTOR = 'td[name="product_template_id"] input.o-autocomplete--input';
const ADD_PRODUCT_SELECTOR = '.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]';
const CONFIG_CONFIRM_SELECTOR = 'button[name="sale_product_configurator_confirm_button"]';

function getRoot() {
    return document.querySelector(ROOT_SELECTOR);
}

function isProductInput(el) {
    return !!el && el.matches && el.matches(PRODUCT_INPUT_SELECTOR);
}

function getAddProductLink() {
    const links = Array.from(document.querySelectorAll(ADD_PRODUCT_SELECTOR));
    return links.find((el) => (el.textContent || '').trim() === 'Produkt hinzufügen' || (el.textContent || '').trim() === 'Add a product') || null;
}

function focusNewestProductInput() {
    window.setTimeout(() => {
        const root = getRoot();
        if (!root) {
            return;
        }
        const inputs = root.querySelectorAll(PRODUCT_INPUT_SELECTOR);
        if (!inputs.length) {
            return;
        }
        const input = inputs[inputs.length - 1];
        input.focus();
        input.click();
    }, 250);
}

function addNextProductLine() {
    const addLink = getAddProductLink();
    if (!addLink) {
        console.log('[sale_input_barcode] add link not found');
        return;
    }
    console.log('[sale_input_barcode] clicking add product link');
    addLink.click();
    focusNewestProductInput();
}

function handleAfterProductAccepted() {
    window.setTimeout(() => {
        const confirmBtn = document.querySelector(CONFIG_CONFIRM_SELECTOR);
        if (confirmBtn && confirmBtn.offsetParent !== null) {
            console.log('[sale_input_barcode] product configurator confirm found, clicking');
            confirmBtn.click();
            window.setTimeout(() => {
                addNextProductLine();
            }, 400);
            return;
        }
        addNextProductLine();
    }, 220);
}

document.addEventListener('keydown', (ev) => {
    const target = ev.target;
    if (!isProductInput(target)) {
        return;
    }
    if (ev.key !== 'Enter') {
        return;
    }

    const root = getRoot();
    if (!root || !target.closest(PRODUCT_CELL_SELECTOR)) {
        return;
    }

    console.log('[sale_input_barcode] Enter on product input', {
        value: target.value,
        expanded: target.getAttribute('aria-expanded'),
        activeDesc: target.getAttribute('aria-activedescendant'),
    });

    window.setTimeout(() => {
        const hasValue = !!(target.value || '').trim();
        const expanded = target.getAttribute('aria-expanded');
        console.log('[sale_input_barcode] post-enter check', {
            hasValue,
            value: target.value,
            expanded,
        });
        if (!hasValue) {
            return;
        }
        if (expanded === 'true') {
            return;
        }
        handleAfterProductAccepted();
    }, 120);
}, true);
