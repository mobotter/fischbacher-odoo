/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class FieldList extends Component {
  static template = "zbsync.mapper.ux.input_data.fieldlist";
  static props = [
    "fieldlist",
    "show_sample_values",
    "root_state",
    "parent",
    "onEnteredItem",
  ];

  setup() {
    this.state = useState({ props: this.props });
  }
}

export class SourceField extends Component {
  static template = "zbsync.mapper.ux.input_data.field";
  static props = [
    "item",
    "show_sample_values",
    "root_state",
    "collapsed?",
    "onEnteredItem",
  ];
  static defaultProps = { collapsed: true };
  // static components = { PauseButton, StringInput, CheckBox, Batch };
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");
    this.rpc = useService("rpc");
    this.values = useState({});
    this.props = useState(this.props);
  }
  get ComponentFieldList() {
    return FieldList;
  }
  dragstart(ev) {
    ev.dataTransfer.setData("ttype", "source_field");
    ev.dataTransfer.setData("mapper_id", this.props.item.mapper_id);
    ev.dataTransfer.setData("name", this.props.item.name);
  }
  async mouseenter() {
    let path = this.props.item.path;
    this.props.root_state.hovered_path = path;
  }
  mouseleave() {
    this.props.root_state.hovered_path = "";
  }

  clicked_item() {
    this.props.onEnteredItem(this.props.item);
  }
}

FieldList.components = { SourceField };
