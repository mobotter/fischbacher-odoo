/** @odoo-module **/

import { registry } from "@web/core/registry";
import {
  Component,
  useState,
  onWillUpdateProps,
  onMounted,
  useSubEnv,
} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { BreadCrumbs } from "./breadcrumb.js";
import { FieldFilter } from "./fieldfilter.js";
import { Outline } from "./outline.js";
import { FieldList } from "./mapper_input_list.js";
import { useRecordObserver } from "@web/model/relational_model/utils";

export class InputData extends Component {
  static template = "zbsync.mapper.ux.input_data.table";
  static supportedTypes = ["text"];
  static components = {
    FieldList,
    CheckBox,
    BreadCrumbs,
    FieldFilter,
    Outline,
  };

  setup() {
    super.setup();
    onMounted(this.parseContentAndBuildModels);
    onWillUpdateProps(this.parseContentAndBuildModels);
    useRecordObserver((record) => {
      this.props.value = record.data[this.props.name];
      this.props.mapper_id = record._config.resId;
    });
    this.orm = useService("orm");
    this.props = useState(this.props);
    this.state = useState({
      show_sample_values: false,
      hovered_path: "init",
      current_parent: null,
      root_fields: [],
      fieldlist: [],
      filter: "",
      actionValues: [],
    });
    useSubEnv({
      get_action_values: async () => {
        if (!this.state.actionValues.length) {
          const model = "zbs.mapping";
          const fields = await this.orm.call("ir.model.fields", "search", [
            [
              ["model_id.model", "=", model],
              ["name", "=", "action"],
            ],
          ]);
          const values = await this.orm.call(
            "ir.model.fields.selection",
            "search_read",
            [[["field_id", "=", fields[0]]], ["value", "name"]],
          );
          let result_dict = {};
          result_dict[null] = "";
          result_dict[undefined] = "";
          for (const row of values) {
            result_dict[row.value] = row.name;
          }
          this.state.actionValues = values;
          this.state.actionValues_dict = result_dict;
        }
        return this.state.actionValues;
      },
      get_action_values_dict: async () => {
        await this.env.get_action_values();
        return this.state.actionValues_dict;
      },
      notify_updated_items: () => {
        this.reparse();
        this.update_preview();
      },
      delete_from_array_by_id: (item, arr) => {
        const index = arr.map((m) => m.id).indexOf(item.id);
        if (index >= 0) {
          arr.splice(index, 1);
          this.env.notify_updated_items();
        }
      },
      append_to_root_fields: (item) => {
        this.state.root_fields.push(item);
        this.reparse();
        this.filter_fields();
      },
      remove_from_root_fields: (item) => {
        this.env.delete_from_array_by_id(item, this.state.root_fields);
        this.reparse();
        this.filter_fields();
      },
      get_current_parent: () => {
        return this.state.current_parent;
      },
      apply_sequences: (new_sequences) => {
        let parents = new Set();
        for (let [item_id, sequence] of Object.entries(new_sequences)) {
          item_id = Number(item_id);
          let item = this.env.find_item_by_id(item_id);
          item.sequence = sequence;
          parents.add(item.parent);
        }
        this.sort_items();
        this.env.notify_updated_items();
      },
      find_item_by_id: (id) => {
        const find = (item) => {
          if (item.id === id) {
            return item;
          }
          if (item.children) {
            for (const child of item.children) {
              let res = find(child);
              if (res) return res;
            }
          }
        };
        for (const item of this.state.root_fields) {
          const found = find(item);
          if (found) {
            return found;
          }
        }
        return null;
      },
    });
  }
  update_preview() {}
  sort_items() {
    const sort = (a, b) => {
      return a.sequence < b.sequence ? -1 : 1;
    };
    this.state.root_fields.sort(sort);

    const sort_children = (parent) => {
      if (!parent.children) {
        return;
      }
      parent.children.sort(sort);
      for (let child of parent.children) {
        sort_children(child);
      }
    };
    for (let child of this.state.root_fields) {
      sort_children(child);
    }
  }

  clicked_current_parent() {
    this.state.current_parent = this.state.current_parent
      ? this.state.current_parent.parent
      : null;
    this.filter_fields();
  }
  filter_fields() {
    if (!this.state.current_parent) {
      this.state.fieldlist = this.state.root_fields;
    } else {
      this.state.fieldlist = this.state.current_parent.children;
    }
    const item_matches = (item) => {
      if (this.state.filter.length === 0) {
        return false;
      }
      return item.name.indexOf(this.state.filter) >= 0;
    };
    // apply filter
    if (this.state.filter) {
      this.state.fieldlist = this.state.fieldlist.filter(item_matches);
    }
    this.update_filter_matchcount(item_matches);
  }
  update_filter_matchcount(item_matches) {
    // reset match counter
    this._iterate_and_exec(
      (item, parent) => {
        item.outline_match_count = 0;
      },
      this.state.root_fields,
      null,
    );

    // mark parents that the container filter matches to show in outline
    this._iterate_and_exec(
      (item, parent) => {
        if (item_matches(item)) {
          if (parent) {
            parent.outline_match_count++;
          }
        }
      },
      this.state.root_fields,
      null,
    );
  }
  _iterate_and_exec(func, items, parent) {
    const inner = (items, parent) => {
      for (let child of items) {
        if (child) {
          func(child, parent);
          if (child.children) {
            inner(child.children, child);
          }
        }
      }
    };
    inner(items, parent);
  }
  _iterate_and_set_parents(items, parent) {
    const self = this;
    this._iterate_and_exec(
      (child, parent) => {
        child.parent = parent;
        child.outline_match_count = 0;
        self.set_functions_in_item(child, parent);
      },
      items,
      parent,
    );
  }
  set_functions_in_item(child) {
    child.is_structure = child.type === "list" || child.type === "object";
    child.outline_name = child.name;
    child.breadcrumb_name = child.name;
  }

  reparse() {
    this._iterate_and_set_parents(this.state.root_fields, null);
  }
  parseContentAndBuildModels(values) {
    const rawValue = values !== undefined ? values.value : this.props.value;
    let content = JSON.parse(rawValue || "[]");
    this.buildModels(content);
  }
  buildModels(content) {
    this.state.fieldlist = [];
    this.state.root_fields = [];
    if (!content || !content.source_fields) {
      return;
    }
    this._iterate_and_set_parents(content.source_fields, null);
    let items = content.source_fields;
    this.state.root_fields = items;
    this.state.fieldlist = items;
  }

  filter_updated(value) {
    this.state.filter = value || "";
    this.filter_fields();
  }
  set_new_parent(parent) {
    this.state.current_parent = parent;
    this.filter_fields();
  }
  breadcrumb_selected(item) {
    if (item) {
      this.set_new_parent(item.parent);
    }
  }
}

const inputData = {
  component: InputData,
  supportedTypes: ["text"],
};
registry.category("fields").add("zbsync_mapper_ux_input", inputData);
