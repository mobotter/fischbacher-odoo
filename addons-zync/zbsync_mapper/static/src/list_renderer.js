/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";

patch(ListRenderer.prototype, {
  setup() {
    super.setup(...arguments);
    this.rpc = useService("orm");
    this.actionService = useService("action");
  },
  async onCellClicked(record, column, ev) {
    var self = this;
    if (record.resModel == "zbs.mapping") {
      if (ev.shiftKey || ev.altKey) {
        var action = await this.rpc.call(record.resModel, "open_mapping", [
          record.data.id,
        ]);
        this.actionService.doAction(action, {
          onClose: () => {
            self.actionService.doAction({
              type: "ir.actions.client",
              tag: "soft_reload",
            });
          },
        });
        return;
      }
    }
    return super.onCellClicked(...arguments);
  },
});
