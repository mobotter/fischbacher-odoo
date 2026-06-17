/** @odoo-module **/

console.log("[sale_input_barcode] auto-next loaded");

const ADD_PRODUCT_SELECTOR =
    '.o_sale_input_barcode_order_line .o_field_x2many_list_row_add a[role="button"]';
const PRODUCT_INPUT_SELECTOR =
    'td[name="product_template_id"] input.o-autocomplete--input';

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
        console.log("[sale_input_barcode] focusing next product input");
        input.value = "";
        input.focus();
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
    console.log("[sale_input_barcode] clicking add product link");
    addLink.click();
    window.setTimeout(() => focusNewestProductInput(), 450);
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

        const expanded = target.getAttribute("aria-expanded");
        const value = (target.value || "").trim();

        console.log(
            "[sale_input_barcode] Enter on product input",
            "value=", value,
            "expanded=", expanded
        );

        if (!value || expanded === "true") {
            return;
        }

        window.setTimeout(() => {
            const currentValue = (target.value || "").trim();
            const currentExpanded = target.getAttribute("aria-expanded");

            console.log(
                "[sale_input_barcode] post-enter check",
                "value=", currentValue,
                "expanded=", currentExpanded
            );

            if (currentValue && currentExpanded !== "true") {
                addNextProductLine();
            }
        }, 300);
    },
    true
);
