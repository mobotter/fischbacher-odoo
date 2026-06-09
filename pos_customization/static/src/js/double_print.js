/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        // Originale Validierung ausführen
        await super.validateOrder(...arguments);

        // Zweiten Druckbefehl nach kurzem Delay auslösen
        // (Delay nötig, damit der erste Druck abgeschlossen ist)
        if (this.env.printer) {
            setTimeout(async () => {
                try {
                    await this.env.printer.printReceipt();
                } catch (e) {
                    console.warn("[double_print] Zweiter Druck fehlgeschlagen:", e);
                }
            }, 2000);
        }
    },
});
