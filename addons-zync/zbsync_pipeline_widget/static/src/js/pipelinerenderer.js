/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillUpdateProps, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { PauseButton } from "./pausebutton";
import { StringInput } from "./stringinput";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { Batch } from "./batch";

export class Worker extends Component {
  static template = "zbsync.pipeline_renderer.worker";
  static props = ["item"];
  static components = { PauseButton, StringInput, CheckBox, Batch };
  values = useState({});
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");
    this.props = useState(this.props);
  }
  dragstart(ev) {
    ev.dataTransfer.setData("line_id", this.props.item.line.id);
  }
  dragover() {}
  async dragdrop(ev) {
    let line_id = ev.dataTransfer.getData("line_id");
    line_id = Number(line_id);
    let dropped_line_id = ev.target.getAttribute("data-lineid");
    if (!dropped_line_id) {
      dropped_line_id = ev.target.parentElement.getAttribute("data-lineid");
    }
    if (!dropped_line_id) {
      dropped_line_id =
        ev.target.parentElement.parentElement.getAttribute("data-lineid");
    }
    dropped_line_id = Number(dropped_line_id);
    await this.rpc("/zync/change_sequence/" + line_id, {
      dropped_on: dropped_line_id,
    });
    this.reload();
  }
  async open_worker() {
    let action = this.orm.call(
      this.props.item.worker.model,
      "open_action",
      [[this.props.item.worker.id]],
      {
        context: {
          zbs_instance_id: this.env.model.root.data.id,
        },
      },
    );
    await this.action.doAction(action);
  }
  async enabled_changed() {
    let new_value = !this.props.item.line.enabled;
    await this.orm.write(
      this.props.item.line.model,
      [this.props.item.line.id],
      { enabled: new_value },
    );
    this.props.item.line.enabled = new_value;
  }
  open_line() {
    var self = this;
    let action = {
      name: "Line",
      view_type: "form",
      res_id: this.props.item.line.id,
      res_model: this.props.item.line.model,
      views: [[false, "form"]],
      type: "ir.actions.act_window",
      target: "new",
    };
    this.action.doAction(action, {
      onClose: () => {
        self.reload();
      },
    });
  }
  show_all_batches() {
    let instance_line_id = this.props.item.line.instance_line_id;
    this.action.doAction({
      name: "Batches of #" + instance_line_id,
      type: "ir.actions.act_window",
      tag: "soft_reload",
      res_model: "zbs.instance.line.batch",
      domain: [["line_id", "=", instance_line_id]],
      views: [
        [false, "list"],
        [false, "form"],
      ],
      target: "current",
    });
  }
  async heartbeat() {
    await this.make_current();
    const instance_id = this.props.item.line.instance_id;
    await this.orm.call("zbs.instance", "heartbeat_ui", [instance_id]);
    await this.reload();
  }
  async make_current() {
    let instance_line_id = this.props.item.line.instance_line_id;
    await this.orm.call("zbs.instance.line", "make_current", [
      instance_line_id,
    ]);
  }

  async reload() {
    await this.action.doAction({
      type: "ir.actions.client",
      tag: "soft_reload",
    });
  }
}

export class WorkerList extends Component {
  static template = "zbsync.pipeline_renderer.worker_list";
  static components = { Worker };
  static props = ["workerlist"];

  setup() {
    super.setup();
    this.props = useState(this.props);
  }
}

export class ZBPipelineRenderer extends Component {
  static template = "zbsync.pipeline_renderer";
  static components = { WorkerList };
  static supportedTypes = ["text"];
  workerlist = useState([]);

  setup() {
    super.setup();
    onMounted(this.parseContentAndBuildModels);
    onWillUpdateProps(this.parseContentAndBuildModels);
  }

  async parseContentAndBuildModels(values) {
    const record = values ? values.record : this.props.record;
    const rawValue = record.data[this.props.name];
    let content = JSON.parse(rawValue || "[]");
    while (this.workerlist.length > 0) {
      this.workerlist.pop();
    }
    for (const [i, item] of content.entries()) {
      item.is_last = i == content.length - 1;
      this.workerlist.push(item);
    }
  }
}

registry.category("fields").add("pipeline_renderer", {
  component: ZBPipelineRenderer,
  supportedTypes: ["text"],
});
