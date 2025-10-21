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
    const target = ev.target;
    let action = null;
    if (
      target &&
      (record.resModel === "zbs.instance.line" ||
        record.resModel === "zbs.pipeline.line")
    ) {
      // if (ev.shiftKey || ev.altKey) {
      if (target.classList.contains("open_line")) {
        action = await this.rpc.call(
          record.resModel,
          "open_line",
          [record.data.id],
          { css_class: target.prop("class") },
        );
      } else if (target.classList.contains("open_batches")) {
        action = await this.rpc.call(record.resModel, "open_batches", [
          record.data.id,
        ]);
      } else {
        // if (target.classList.contains("open_action")) {
        let id = record.data.worker_id.resId;
        let model = record.data.worker_id.resModel;
        action = await this.rpc.call(model, "open_action", [id], {
          context: record.context,
        });
      }

      if (action) {
        this.actionService.doAction(action, {
          onClose: async (ev) => {
            await record.model.root.load();
            record.model.notify();
          },
        });
        return;
      }
    }
    super.onCellClicked(...arguments);
  },
});
