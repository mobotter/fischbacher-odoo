/** @odoo-module **/

console.log("[sale_input_barcode] DOM auto-next loaded");

const ROOT_SELECTOR = '.o_sale_input_barcode_order_line';
const PRODUCT_CELL_SELECTOR = 'td[name="product_template_id"]';
const PRODUCT_INPUT_SELECTOR = 'td[name="product_template_id"] input.o-autocomplete--input';
const ADD_PRODUCT_SELECTOR = '.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]';
const CONFIG_CONFIRM_SELECTOR = 'button[name="sale_product_configurator_confirm_button"]';
const COOLDOWN_MS = 1100;
let processing = false;
let lastProcessedValue = '';
let lastProcessedAt = 0;

function getRoot() {
    return document.querySelector(ROOT_SELECTOR);
}

function isProductInput(el) {
    return !!el && el.matches && el.matches(PRODUCT_INPUT_SELECTOR);
}

function getAddProductLink() {
    const links = Array.from(document.querySelectorAll(ADD_PRODUCT_SELECTOR));
    return links.find((el) => {
        const text = (el.textContent || '').trim();
        return text === 'Produkt hinzufügen' || text === 'Add a product' || text === 'Produkt hinzufügen';
    }) || null;
}

function getNewestProductInput() {
    const root = getRoot();
    if (!root) return null;
    const inputs = root.querySelectorAll(PRODUCT_INPUT_SELECTOR);
    return inputs.length ? inputs[inputs.length - 1] : null;
}

function focusNewestProductInput(retries = 10) {
    const tryFocus = () => {
        const input = getNewestProductInput();
        if (input) {
            input.focus();
            input.click();
            processing = false;
            return;
        }
        if (retries > 0) {
            window.setTimeout(() => focusNewestProductInput(retries - 1), 150);
        } else {
            processing = false;
        }
    };
    window.setTimeout(tryFocus, 450);
}

function addNextProductLine() {
    const addLink = getAddProductLink();
    if (!addLink) {
        console.log('[sale_input_barcode] add link not found');
        processing = false;
        return;
    }
    console.log('[sale_input_barcode] clicking add product link');
    addLink.click();
    focusNewestProductInput();
}

function looksLikeResolvedProduct(value) {
    if (!value) return false;
    const v = String(value).trim();
    if (!v) return false;
    if (/^MIET\d+/i.test(v)) return false;
    if (v.length < 12) return false;
    return /\s-\s/.test(v) || /[A-Za-zÄÖÜäöüß]{3,}/.test(v);
}

function shouldIgnore(value) {
    const now = Date.now();
    if (processing) return true;
    if (now - lastProcessedAt < COOLDOWN_MS) return true;
    if (value && value === lastProcessedValue) return true;
    return false;
}

function handleAfterProductAccepted(target) {
    window.setTimeout(() => {
        const current = (target.value || '').trim();
        const expanded = target.getAttribute('aria-expanded');
        if (expanded === 'true') {
            processing = false;
            return;
        }
        if (!looksLikeResolvedProduct(current)) {
            processing = false;
            return;
        }
        lastProcessedValue = current;
        lastProcessedAt = Date.now();
        const confirmBtn = document.querySelector(CONFIG_CONFIRM_SELECTOR);
        if (confirmBtn && confirmBtn.offsetParent !== null) {
            console.log('[sale_input_barcode] product configurator confirm found, clicking');
            confirmBtn.click();
            window.setTimeout(() => {
                addNextProductLine();
            }, 650);
            return;
        }
        addNextProductLine();
    }, 220);
}

document.addEventListener('keydown', (ev) => {
    const target = ev.target;
    if (!isProductInput(target)) return;
    if (ev.key !== 'Enter') return;
    const root = getRoot();
    if (!root || !target.closest(PRODUCT_CELL_SELECTOR)) return;
    if (shouldIgnore(target.value || '')) return;
    processing = true;
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
        if (!hasValue || expanded === 'true') {
            processing = false;
            return;
        }
        handleAfterProductAccepted(target);
    }, 180);
}, true);
