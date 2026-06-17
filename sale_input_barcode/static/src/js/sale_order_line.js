/** @odoo-module **/

const ADD_PRODUCT_SELECTOR =
    '.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]';
const PRODUCT_INPUT_SELECTOR =
    'td[name="product_template_id"] input.o-autocomplete--input';

let ignoreEnterUntil = 0;
let autoSelecting = false;

function getAddProductLink() {
    const links = Array.from(document.querySelectorAll(ADD_PRODUCT_SELECTOR));
    return (
        links.find((el) => {
            const text = (el.textContent || "").trim();
            return text === "Produkt hinzufügen" || text === "Add a product";
        }) || null
    );
}

function getNewestProductInput() {
    const inputs = document.querySelectorAll(PRODUCT_INPUT_SELECTOR);
    return inputs.length ? inputs[inputs.length - 1] : null;
}

function focusNewestProductInput(retries = 12) {
    const input = getNewestProductInput();
    if (input) {
        input.value = "";
        input.focus();
        ignoreEnterUntil = Date.now() + 1200;
        return;
    }
    if (retries > 0) {
        window.setTimeout(() => focusNewestProductInput(retries - 1), 150);
    }
}

function addNextProductLine() {
    const addLink = getAddProductLink();
    if (!addLink) {
        return;
    }
    addLink.click();
    window.setTimeout(() => focusNewestProductInput(), 450);
}

function getActiveOption(input) {
    const activeId = input.getAttribute("aria-activedescendant");
    if (activeId) {
        const el = document.getElementById(activeId);
        if (el) {
            return el;
        }
    }
    return document.querySelector(".ui-menu-item-wrapper.ui-state-active, .dropdown-item.active, [role='option'][aria-selected='true']");
}

function tryAutoSelect(input, retries = 12) {
    if (!input || autoSelecting) {
        return;
    }

    const expanded = input.getAttribute("aria-expanded");
    const option = getActiveOption(input);

    if (expanded === "true" && option) {
        autoSelecting = true;
        option.click();

        window.setTimeout(() => {
            autoSelecting = false;

            const currentValue = (input.value || "").trim();
            const currentExpanded = input.getAttribute("aria-expanded");

            if (currentValue && currentExpanded !== "true") {
                addNextProductLine();
            }
        }, 350);
        return;
    }

    if (retries > 0) {
        window.setTimeout(() => tryAutoSelect(input, retries - 1), 120);
    }
}

document.addEventListener(
    "keydown",
    (ev) => {
        const target = ev.target;
        if (!(target instanceof HTMLInputElement)) {
            return;
        }
        if (!target.matches(PRODUCT_INPUT_SELECTOR)) {
            return;
        }
        if (ev.key !== "Enter") {
            return;
        }

        if (Date.now() < ignoreEnterUntil) {
            ev.preventDefault();
            ev.stopPropagation();
            return;
        }

        const value = (target.value || "").trim();

        if (!value) {
            return;
        }

        window.setTimeout(() => {
            const currentValue = (target.value || "").trim();
            const currentExpanded = target.getAttribute("aria-expanded");

            if (!currentValue) {
                return;
            }

            if (currentExpanded === "true") {
                tryAutoSelect(target);
                return;
            }

            addNextProductLine();
        }, 250);
    },
    true
);
