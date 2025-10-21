/** @odoo-module **/

import { useState, xml, useRef, useEffect } from "@odoo/owl";
import { UpdateLine } from "./updateline";

export class StringInput extends UpdateLine {
  static template = xml`
    <t t-if="this.values.mode == 'read'">
		<div
			t-on-click="clicked_span"
			class="zbpipeline-string-input-hover"
		>
		<t t-esc="this.recordvalue.value"/>
		</div>
    </t>
    <t t-else="">
        <input
			t-att-placeholder="this.props.placeholder"
			t-model="this.recordvalue.value"
			t-on-change="changed"
			t-on-blur="changed"
			t-on-keydown="keydown"
			t-ref="input1"
		/>
    </t>
    `;
  setup() {
    super.setup();
    // this.props = {...{ placeholder: {optional: true}}, ...this.props};
    this.input1 = useRef("input1");
    // quasi autofocus
    useEffect(
      (el) => el && el.focus(),
      () => [this.input1.el],
    );
  }
  values = useState({ text: "", mode: "read" });
  async update_db() {
    super.update_db();
    this.values.mode = "read";
  }
  async changed() {
    await this.update_db();
  }
  repr() {
    this.values.text = this.recordvalue.value;
  }
  clicked_span() {
    this.values.mode = "write";
  }
  keydown(ev) {
    if (ev.key == "Escape") {
      ev.target.blur();
    }
  }
}
StringInput.props = {
  ...UpdateLine.props,
  placeholder: { optional: true },
};
