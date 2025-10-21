/** @odoo-module **/
//https://codepen.io/st-iv/pen/YzPpPYG

import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { useAutofocus } from "@web/core/utils/hooks";

export class MappingProperty extends Component {
  static template = "zbsync.mapper.ux.mapping_data.mapping.property";
  static props = ["item", "fieldname", "type?"];
  state = useState({
    edit_mode: false,
    selectionValues: [],
    stringvalue: "",
  });
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");
    this.props = useState(this.props);
    this.inputRef = useAutofocus();
    onWillUpdateProps(this.update_props);
    this.update_props(this.props);
  }
  async update_props(props) {
    const value = props.item[props.fieldname];
    const actions = await this.env.get_action_values();
    await this.update_stringvalue(props);
    this.state.selectionValues = [];
    for (const action of actions) {
      this.state.selectionValues.push(action);
    }
  }
  async savechanges() {
    let value = "";
    if (this.props.type === "selection") {
      value = this.inputRef.el.value;
    } else {
      value = this.inputRef.el.value;
    }
    const fieldname = this.props.fieldname;
    const data = {};
    data[fieldname] = value;
    await this.orm.call("zbs.mapping", "write", [[this.props.item.id], data]);
    this.props.item[this.props.fieldname] = value;
    await this.update_stringvalue(this.props);
    this.state.edit_mode = false;
    this.env.notify_updated_items();
  }

  enter_editmode() {
    this.state.edit_mode = true;
    const self = this;
  }

  async update_stringvalue(props) {
    let value = props.item[props.fieldname];
    if (props.type === "selection") {
      const d = await this.env.get_action_values_dict();
      this.state.stringvalue = d[value];
    } else {
      this.state.stringvalue = value;
    }
  }
}
