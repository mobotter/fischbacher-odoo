/** @odoo-module */

import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/patch";

/**
 * Patch ReceiptScreen, um den Kassenbon automatisch 2x zu drucken.
 * Nach dem Bestellen wird der ReceiptScreen angezeigt und der Druck-Befehl
 * wird automatisch zweimal ausgelöst.
 */

patch(ReceiptScreen.prototype, {
    /**
     * Überschreibt die validatePayment-Methode, um nach dem ersten Druck
     * automatisch einen zweiten Druck auszulösen.
     */
    async validatePayment() {
        // Erster Druck (Original-Verhalten)
        await super.validatePayment();

        // Zweiter Druck - kurz verzögert, damit der erste Druck abgeschlossen ist
        setTimeout(() => {
            this.env.pos.printReceipt();
        }, 1000);
    },
});
