/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, xml } from "@odoo/owl";

export class Preview extends Component {
  static template = xml`<div><t t-esc="props.preview"/></div>`;
  static props = ["preview"];
  setup() {
    this.props = useState(this.props);
  }
}

const preview = {
  component: Preview,
};
registry.category("fields").add("mapping_ux_preview", preview);
