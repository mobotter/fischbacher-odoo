/** @odoo-module **/

import { useState, xml } from "@odoo/owl";
import { UpdateLine } from "./updateline";

export class PauseButton extends UpdateLine {
  static template = xml`<img t-att-src="values.url" width="20" t-on-click="clicked"/>`;
  values = useState({ url: "" });
  async clicked() {
    this.recordvalue.value = !this.recordvalue.value;
    await this.update_db();
    this.setup_image();
  }
  repr() {
    this.setup_image();
  }
  setup_image() {
    let value = this.recordvalue.value;
    let url = "/zbsync_pipeline_widget/static/img/";
    if (value) {
      url += "fast_forward.png";
    } else {
      url += "pause.png";
    }
    this.values.url = url;
  }
}
