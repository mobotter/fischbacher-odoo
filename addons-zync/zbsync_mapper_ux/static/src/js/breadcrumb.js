/** @odoo-module **/

import { Component, useState, xml, onWillUpdateProps } from "@odoo/owl";

export class BreadCrumbs extends Component {
  static template = xml`<div class="breadcrumbs">
		<t t-foreach="state.crumbs" t-as="crumb" t-key="crumb.id">
			<span class="divider" t-if="!crumb.is_breadcrumb_last">
			/
			</span>
			<span class="breadcrumb" t-on-click="clicked_item" t-att-data-id="crumb.id">
			<t t-esc="crumb.breadcrumb_name"/>
			</span>
		</t>
	</div>`;
  static props = ["parent", "onSelect"];
  // static components = { PauseButton, StringInput, CheckBox, Batch };
  setup() {
    this.props = useState(this.props);
    this.state = useState({ crumbs: [] });
    onWillUpdateProps(this.parse_path);
  }
  parse_path(props) {
    this.state.crumbs = [];
    let p = props.parent;
    while (p) {
      this.state.crumbs.unshift(p);
      let last_p = p;
      p.is_breadcrumb_last = false;
      p = p.parent;
      if (!p) {
        last_p.is_breadcrumb_last = true;
      }
    }
  }
  clicked_item(ev) {
    let id = ev.target.dataset.id;
    if (!isNaN(id)) {
      id = Number(id);
    }
    const item = this.env.find_item_by_id(id);
    this.props.onSelect(item);
  }
}
