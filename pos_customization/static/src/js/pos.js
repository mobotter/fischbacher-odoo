/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments); // In Odoo 19 arguments weiterreichen
        this.hardwareproxy = useService("hardware_proxy");
    },

    async openDrawer() {
        try {
            // Versuche direkt das Kassensignal über den Drucker (Hardware Proxy) zu senden
            if (this.hardwareProxy.printer) {
                await this.hardwareProxy.printer.openCashbox();
            } else {
                // Fallback, falls Odoo IoT die Kasse direkt steuert
                await this.hardwareProxy.openCashbox();
            }
        } catch (error) {
            console.error("Error while opening cash drawer:", error);
        }
    }
});
