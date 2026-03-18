/** @odoo-module **/

import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments); // In Odoo 19 arguments weiterreichen
        this.hardwareproxy = useService("hardware_proxy");
    },

    async OpenDrawer() {
        try {
            await this.hardwareproxy.openCashbox();
            console.log("Cashbox opened via OpenDrawer");
        } catch (error) {
            console.error("Error in OpenDrawer:", error);
        }
    }
});
