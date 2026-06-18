/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        // Originale Validierung ausführen
        await super.validateOrder(...arguments);

        // Direkter doppelter Druck ohne Delay
        if (this.env.printer) {
            try {
                // Erstes BON
                await this.env.printer.printReceipt();

                // Minimaler Delay nur für Printer-Puffer
                // await new Promise(resolve => setTimeout(resolve, 100));
                
                // Zweites BON direkt danach (ohne Delay)
                await this.env.printer.printReceipt();
            } catch (e) {
                console.warn("[double_print] Druck fehlgeschlagen:", e);
            }
        }
    },
});
