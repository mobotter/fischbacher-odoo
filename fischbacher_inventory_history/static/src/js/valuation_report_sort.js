/** @odoo-module **/

const collator = new Intl.Collator("de", { numeric: true, sensitivity: "base" });
const sortStates = new WeakMap();

function sortValuationTable(event) {
    const target = event.target;
    if (!(target instanceof Element)) {
        return;
    }
    const button = target.closest("button[data-fh-sort]");
    if (!button) {
        return;
    }
    const table = button.closest("table.fh-valuation-sortable");
    const header = button.closest("th");
    if (!table || !header || header.closest("table") !== table || !table.tBodies.length) {
        return;
    }
    const body = table.tBodies[0];
    const column = header.cellIndex;
    const previous = sortStates.get(table);
    const direction = previous && previous.column === column && previous.direction === 1 ? -1 : 1;
    const numeric = button.dataset.fhSort === "number";
    const rows = Array.from(body.rows).map((row, index) => {
        const cell = row.cells[column];
        const raw = cell ? (cell.dataset.fhSortValue ?? cell.textContent.trim()) : "";
        const value = numeric ? (raw === "" ? null : Number(raw)) : raw;
        const missing = numeric ? value === null || !Number.isFinite(value) : raw === "";
        return { row, index, value, missing };
    });
    rows.sort((a, b) => {
        if (a.missing !== b.missing) {
            return a.missing ? 1 : -1;
        }
        if (a.missing) {
            return a.index - b.index;
        }
        const comparison = numeric ? a.value - b.value : collator.compare(a.value, b.value);
        return comparison ? direction * comparison : a.index - b.index;
    });
    const fragment = document.createDocumentFragment();
    for (const item of rows) {
        fragment.appendChild(item.row);
    }
    body.appendChild(fragment);
    sortStates.set(table, { column, direction });
    for (const th of table.tHead.rows[0].cells) {
        th.setAttribute("aria-sort", "none");
        const indicator = th.querySelector("[data-fh-sort-indicator]");
        if (indicator) {
            indicator.textContent = "↕";
        }
    }
    header.setAttribute("aria-sort", direction === 1 ? "ascending" : "descending");
    const indicator = button.querySelector("[data-fh-sort-indicator]");
    if (indicator) {
        indicator.textContent = direction === 1 ? "↑" : "↓";
    }
}

// Delegation handles newly rendered report tables without per-row listeners.
document.addEventListener("click", sortValuationTable);
