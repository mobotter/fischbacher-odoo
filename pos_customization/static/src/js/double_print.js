/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;

        // Guard: Falls keine Order vorhanden ist, normal validieren
        if (!order) {
            return await super.validateOrder(...arguments);
        }

        // Guard gegen doppelte Ausführung auf derselben Order
        if (order._doubleReceiptPrinted) {
            return await super.validateOrder(...arguments);
        }

        // Standard-Validierung inkl. normalem Odoo-Receipt-Flow
        await super.validateOrder(...arguments);

        // Nach erfolgreicher Validierung genau EINE Zusatzkopie drucken
        if (this.env.printer) {
            try {
                order._doubleReceiptPrinted = true;

                // Kleiner Buffer-Delay für manche Netzwerk-/ePOS-Drucker
                await new Promise((resolve) => setTimeout(resolve, 250));

                await this.env.printer.printReceipt();
            } catch (e) {
                console.warn("[double_print] Zweiter Bon fehlgeschlagen:", e);
                order._doubleReceiptPrinted = false;
            }
        }
    },
});
