/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";


/**
 * Öffnet die Kassenlade über IoT-/Hardware-Proxy.
 */
patch(ControlButtons.prototype, {
    async openDrawer() {
        try {
            const hardwareProxy = this.pos.hardwareProxy;

            if (hardwareProxy?.printer?.openCashbox) {
                await hardwareProxy.printer.openCashbox();
                return;
            }

            if (hardwareProxy?.openCashbox) {
                await hardwareProxy.openCashbox();
                return;
            }

            console.warn(
                "[pos_customization] Kein aktiver Hardware-Proxy bzw. kein Kassenladen-Drucker konfiguriert."
            );
        } catch (error) {
            console.error(
                "[pos_customization] Fehler beim Öffnen der Kassenlade:",
                error
            );
        }
    },
});
