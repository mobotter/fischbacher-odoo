/** @odoo-module **/

import { Component, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class Batch extends Component {
  static template = xml`
        <div t-attf-class="zbs-batch #{props.batch.state}" t-on-click.stop="clicked" style="cursor: pointer;">
            <t t-esc="props.batch.length"/> Record(s) in <t t-esc="props.batch.count"/> Batches
        </div>
    `;
  static props = ["batch"];
  static components = {};
  values = useState({});
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");
  }
  async clicked() {
    const domain = [
      "&",
      ["line_id", "=", this.props.batch.line_id],
      ["state", "=", this.props.batch.state],
    ];

    let ids = await this.orm.call("zbs.instance.line.batch", "search", [
      domain,
    ]);
    const action = {
      name: "Batches",
      view_type: "form",
      res_model: "zbs.instance.line.batch",
      views: [
        [null, "list"],
        [null, "form"],
      ],
      type: "ir.actions.act_window",
      domain: ["|", ["id", "in", ids]].concat(domain),
      context: {
        form_view_initial_mode: "edit",
      },
      target: "current",
    };
    this.action.doAction(action);
  }
}
