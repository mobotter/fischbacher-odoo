/** @odoo-module **/

import { Component, useState, xml } from "@odoo/owl";

export class FieldFilter extends Component {
  static template = xml`<span class="field-filter">
		<input t-on-keyup="update_filter"/>
	</span>`;
  static props = ["onNewFilter"];
  setup() {
    this.props = useState(this.props);
    this.state = useState({ crumbs: [] });
  }
  update_filter(ev) {
    const value = ev.target.value;
    this.props.onNewFilter(value);
  }
}
