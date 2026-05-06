/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        // Kein useService mehr nötig, wir greifen direkt über this.pos darauf zu
    },

    async openDrawer() {
        try {
            // In Odoo POS ist die globale POS-Instanz in der Komponente als this.pos verfügbar
            // Über diese greifen wir auf hardwareProxy bzw. den printer zu
            if (this.pos.hardwareProxy && this.pos.hardwareProxy.printer) {
                await this.pos.hardwareProxy.printer.openCashbox();
            } else if (this.pos.hardwareProxy) {
                await this.pos.hardwareProxy.openCashbox();
            } else {
                console.warn("Hardware Proxy ist in der aktuellen POS-Sitzung nicht konfiguriert oder aktiv.");
            }
        } catch (error) {
            console.error("Error while opening cash drawer:", error);
        }
    }
});
