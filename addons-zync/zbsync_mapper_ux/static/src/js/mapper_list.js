/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { MappingProperty } from "./mapping_property.js";

const CSS_CLASS_DROPACTIVE = "drop-active";

export class MappingList extends Component {
  static template = "zbsync.mapper.ux.mapping_data.mappinglist";
  static props = ["mappinglist", "mapping_id", "mapper_id", "onEnteredItem"];
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");
    this.state = useState({
      addmapping_dropklass: "",
    });
  }

  async append_just_created_mapping(mapping_id) {
    const data = await this.env.read_from_db(mapping_id);
    data.children = [];
    if (data.parent_id) {
      const parent_id = data.parent_id[0];
      const parent = this.env.find_item_by_id(parent_id);
      data.parent = parent;
      parent.children.push(data);
    } else {
      this.env.append_to_root_fields(data);
    }
    this.env.notify_updated_items();
  }

  async add() {
    let mapper_id = Number(this.props.mapper_id);
    let mapping_id = Number(this.props.mapping_id);
    const step_id = mapper_id;
    const parent_id = this.env.get_current_parent()
      ? this.env.get_current_parent().id
      : false;
    let action = await this.orm.call("zbs.mapping", "open_mapping", [[]], {
      context: {
        mapper_id: mapper_id,
        default_step_id: mapper_id,
        default_parent_id: mapping_id || false,
      },
    });
    action.target = "new";
    var self = this;
    const last_mapping_before = await this.get_last_mapping(step_id, parent_id);
    await this.action.doAction(action, {
      onClose: async () => {
        const last_mapping = await this.get_last_mapping(step_id, parent_id);
        if (last_mapping != last_mapping_before) {
          self.append_just_created_mapping(last_mapping);
        }
      },
    });
  }
  async get_last_mapping(step_id, parent_id) {
    const mappings = await this.orm.call(
      "zbs.mapping",
      "search",
      [
        [
          ["step_id", "=", step_id],
          ["parent_id", "=", parent_id],
        ],
      ],
      { order: "id desc", limit: 1 },
    );

    return mappings;
  }

  async dragenter_addmapping() {
    this.state.show_dropzone = true;
    this.state.addmapping_dropklass = CSS_CLASS_DROPACTIVE;
  }
  async dragleave_addmapping() {
    this.state.show_dropzone = false;
    this.state.addmapping_dropklass = "";
  }
  set_new_parent(item) {
    this.props.onEnteredItem(item);
  }

  async dropped_addmapping(ev) {
    if (ev.dataTransfer.getData("ttype") == "source_field") {
      let name = ev.dataTransfer.getData("name");
      let parent_id = this.props.mapping_id || false;
      let mapper_id = Number(ev.dataTransfer.getData("mapper_id"));
      let mapping_id = await this.orm.call("zbs.mapping", "create", [
        {
          step_id: mapper_id,
          parent_id: parent_id,
          field_source: name,
          field_dest: name,
        },
      ]);
      let action = await this.orm.call(
        "zbs.mapping",
        "open_mapping",
        [[mapping_id]],
        {
          context: {
            mapper_id: mapper_id,
          },
        },
      );
      this.dragleave_addmapping();
      action.target = "new";
      let self = this;
      await this.action.doAction(action, {
        onClose: async () => {
          self.append_just_created_mapping(mapping_id);
        },
      });
    }
  }
}

export class Mapping extends Component {
  static template = "zbsync.mapper.ux.mapping_data.mapping";
  static props = ["item", "mapping_id", "mapper_id", "onEnteredItem"];
  static components = { MappingProperty };
  state = useState({
    edit_mode: false,
  });
  setup() {
    this.action = useService("action");
    this.orm = useService("orm");
    this.props = useState(this.props);
  }
  get ComponentMappingList() {
    return MappingList;
  }

  get is_structure() {
    return this.props.item.is_structure;
  }
  clicked_extlink() {
    return this.dblclicked_item();
  }
  clicked_item(fieldname) {
    if (!this.state.edit_mode) {
      this.state.edit_mode = fieldname;
    } else {
      this.state.edit_mode = false;
    }
  }
  dblclicked_item() {
    if (this.props.item.is_structure) {
      this.props.onEnteredItem(this.props.item);
    } else {
      this.open_line();
    }
    return true;
  }
  async delete() {
    await this.orm.call("zbs.mapping", "unlink", [[this.props.item.id]]);
    if (this.props.item.parent) {
      let children = this.props.item.parent.children;
      this.env.delete_from_array_by_id(this.props.item, children);
      this.env.notify_updated_items();
    } else {
      this.env.remove_from_root_fields(this.props.item);
    }
  }

  async open_line() {
    let action = await this.orm.call(
      "zbs.mapping",
      "open_mapping",
      [[this.props.item.id]],
      {
        context: {
          mapper_id: this.props.mapper_id,
        },
      },
    );
    action.target = "new";
    const self = this;
    await this.action.doAction(action, {
      onClose: async () => {
        let item = self.env.find_item_by_id(self.props.item.id);
        if (item) {
          let db = await self.env.read_from_db(item.id);
          item.field_source = db.field_source;
          item.field_dest = db.field_dest;
          item.action = db.action;
        }
        self.env.notify_updated_items();
      },
    });
  }
  async on_drop(ev) {
    // for sequences
    for (const el of document.getElementsByClassName("dropzone-bottom")) {
      el.classList.remove("dropzone-bottom");
    }
    const dropped_on = ev.currentTarget.dataset.id;
    const source = ev.dataTransfer.getData("id");
    if (!source || !dropped_on) {
      return;
    }
    const new_sequences = await this.orm.call(
      "zbs.mapping",
      "ui_dropped",
      [[this.props.item.id], source],
      {},
    );
    this.env.apply_sequences(new_sequences);
  }
  drag_end(ev) {
    ev.currentTarget.style.opacity = "1.0";
  }
  drag_start(ev) {
    ev.currentTarget.style.opacity = "1.4";
    ev.dataTransfer.setData("id", ev.currentTarget.dataset.id);
  }
  dragover_item_sequence(ev) {
    const target = ev.currentTarget;
    if (target.classList.contains("mapping")) {
      target.classList.add("dropzone-bottom");
    }
  }
  dragleave_item_sequence(ev) {
    const target = ev.currentTarget;
    target.classList.remove("dropzone-bottom");
  }
}
MappingList.components = { Mapping };
MappingList.components = { Mapping };
