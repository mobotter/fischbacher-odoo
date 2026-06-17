/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(FormController.prototype, {
    async action_open_barcode_scanner_dialog() {
        if (this.props.resModel !== "sale.order") {
            return;
        }
        this.dialogService.add(ConfirmationDialog, {
            title: "Scan product barcode",
            body: "Focus the scanner now. The next scan will create a new sale order line.",
            confirmLabel: "Cancel",
            cancelLabel: "",
            confirm: () => {},
        });

        const handler = async (ev) => {
            if (this.props.resModel !== "sale.order") {
                return;
            }
            if (ev.key !== "Enter") {
                return;
            }
            const value = (window.__saleBarcodeBuffer || "").trim();
            window.__saleBarcodeBuffer = "";
            if (!value) {
                return;
            }
            window.removeEventListener("keydown", capture, true);
            await this.model.root.orm.call("sale.order", "action_add_product_by_barcode", [[this.props.resId], value]);
            await this.model.root.load();
            this.render(true);
        };

        const capture = (ev) => {
            if (ev.key === "Shift" || ev.key === "Control" || ev.key === "Alt") {
                return;
            }
            if (ev.key === "Enter") {
                ev.preventDefault();
                handler(ev);
                return;
            }
            if (ev.key.length === 1) {
                window.__saleBarcodeBuffer = (window.__saleBarcodeBuffer || "") + ev.key;
            }
        };

        window.__saleBarcodeBuffer = "";
        window.addEventListener("keydown", capture, true);
    },
});
