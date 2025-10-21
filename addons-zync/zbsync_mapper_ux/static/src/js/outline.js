/** @odoo-module **/

import { Component, useState, onWillUpdateProps } from "@odoo/owl";

const INDENT = 12;

export class OutlineElement extends Component {
  static props = [
    "padding",
    "name",
    "current?",
    "id",
    "match_count",
    "onSelect",
  ];
  static defaultProps = { current: false };
  static template = "zbsync.mapper.ux.outline";

  clicked(ev) {
    let id = ev.target.dataset.id;
    if (!isNaN(Number(id))) {
      id = Number(id);
    }
    this.props.onSelect(id);
  }
}

export class Outline extends Component {
  static components = { OutlineElement };
  static template = "zbsync.mapper.ux.outline.parent";
  static props = ["fields", "current_item", "onSelect"];
  setup() {
    this.props = useState(this.props);
    this.state = useState({ elements: [] });
    onWillUpdateProps((props) => {
      this.parseFields(props.fields, props.current_item);
    });
  }
  onSelect(id) {
    const item = this.env.find_item_by_id(id);
    this.props.onSelect(item);
  }
  parseFields(fields, current_item) {
    let root_element = {
      id: "outline_root",
      outline_name: "root",
      indent: 0,
      path: null,
    };
    this.state.elements = [root_element];
    const current_id = current_item ? current_item.id : null;

    const crit = (item) => {
      return item.is_structure ? item.is_structure : false;
    };
    let found_current = false;
    const add_child = (item, indent, parent) => {
      if (item.id == "outline_root" || crit(item)) {
        item.outline_indent = indent;
        this.state.elements.push(item);
        item.outline_parent = parent;
        item.outline_current = item.id === current_id;
        if (item.outline_current) {
          found_current = true;
        }
      }
      for (const child of item.children) {
        add_child(child, indent + 1, item);
      }
    };
    for (const element of fields) {
      add_child(element, 1, root_element);
    }
    root_element.outline_current = !found_current;

    for (const item of this.state.elements) {
      item.outline_padding = INDENT * item.outline_indent;
    }
  }
}
