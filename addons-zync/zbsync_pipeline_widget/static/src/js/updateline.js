/** @odoo-module **/

import { Component, useState, onWillUpdateProps, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class UpdateLine extends Component {
  static props = {
    recordid: {},
    fieldname: {},
    record: {},
    model: {},
    ttype: { optional: true },
  };
  static defaultProps = {
    ttype: "string",
  };
  recordvalue = useState({ value: true });
  setup() {
    this.orm = useService("orm");
    this.recordvalue.value = this.props.record[this.props.fieldname];
    if (this.props.ttype === "string" && !this.recordvalue.value) {
      this.recordvalue.value = "";
    }
    onMounted(() => {
      this.repr();
    });
    onWillUpdateProps((newvals) => {
      this.recordvalue.value = newvals.record[this.props.fieldname];
      this.repr();
    });
  }
  getDBValue() {
    let res = this.recordvalue.value;
    if (this.props.ttype.toLowerCase() == "number") {
      if (typeof res === "string" || res instanceof String) {
        res = (res || "").trim();
      }
      if (isNaN(res)) {
        throw Error("Invalid: " + res);
      }
      res = Number(res);
    } else if (this.props.ttype.toLowerCase() === "string") {
      // pass
    } else {
      throw Error("Invalid: " + this.props.ttype);
    }
    return res;
  }
  async on_value_update() {
    this.update_db();
  }
  repr() {}

  async update_db() {
    let fieldname = this.props.fieldname;
    let value = {};
    value[fieldname] = this.getDBValue();
    await this.orm.write(this.props.model, [this.props.recordid], value);
  }
}
