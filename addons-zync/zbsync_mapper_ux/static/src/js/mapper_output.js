/** @odoo-module **/

import { registry } from "@web/core/registry";
import { onWillUpdateProps, useSubEnv } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { InputData } from "./mapper_input.js";
import { Outline } from "./outline.js";
import { FieldFilter } from "./fieldfilter.js";
import { BreadCrumbs } from "./breadcrumb.js";
import { MappingList } from "./mapper_list.js";
import { Preview } from "./preview.js";
import { useRecordObserver } from "@web/model/relational_model/utils";

export class MappingData extends InputData {
  static components = {
    MappingList,
    Outline,
    FieldFilter,
    BreadCrumbs,
    Preview,
  };
  static template = "zbsync.mapper.ux.mapping_data.table";
  setup() {
    super.setup();
    this.orm = useService("orm");
    this.state.show_dropzone = false;
    useSubEnv({
      read_from_db: async (mapping_id) => {
        let data = (
          await this.orm.call("zbs.mapping", "read", [
            mapping_id,
            ["field_source", "field_dest", "action", "sequence", "parent_id"],
          ])
        )[0];
        return data;
      },
    });
    onWillUpdateProps(() => {
      console.log("hier");
    });
    useRecordObserver((record) => {});
  }
  set_functions_in_item(child) {
    child.is_structure = child.action === "list" || child.action === "object";
    child.outline_name = this.get_outline_name(child);
    child.breadcrumb_name = this.get_breadcrumb_name(child);
  }
  get_outline_name(item) {
    if (item.action === "list") {
      return "[] --> " + item.field_dest;
    } else if (item.action === "object") {
      return "{} --> " + item.field_dest;
    }
    return item.field_source + " --> " + item.field_dest;
  }
  get_breadcrumb_name(item) {
    return this.get_outline_name(item);
  }
  filter_fields() {
    if (!this.state.current_parent) {
      this.state.fieldlist = this.state.root_fields;
    } else {
      this.state.fieldlist = this.state.current_parent.children;
    }
    const item_matches = (item) => {
      const filter = this.state.filter;
      if (!filter.length) {
        return false;
      }
      if ((item.field_source || "").indexOf(filter) >= 0) {
        return true;
      }
      if ((item.field_dest || "").indexOf(filter) >= 0) {
        return true;
      }
      return false;
    };
    // apply filter
    if (this.state.filter) {
      this.state.fieldlist = this.state.fieldlist.filter(item_matches);
    }
    this.update_filter_matchcount(item_matches);
  }
  async update_preview() {
    const mapper_id = this.props.mapper_id;
    const record = (
      await this.orm.call("zbs.mapper", "read", [[mapper_id], ["ux_version"]])
    )[0];
    await this.orm.call("zbs.mapper", "write", [
      [mapper_id],
      { ux_version: record.ux_version + 1 },
    ]);
    const preview = (
      await this.orm.call("zbs.mapper", "read", [[mapper_id], ["ux_preview"]])
    )[0].ux_preview;
    // dirty as its bets
    document.getElementsByName("ux_preview")[0].children[0].innerHTML = preview;
  }
}

const mappingData = {
  component: MappingData,
};
registry.category("fields").add("zbsync_mapper_ux_mapping", mappingData);
