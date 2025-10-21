from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FieldTrigger(models.Model):
    _inherit = ["method_hook.trigger.mixin"]
    _name = "method_hook.field_trigger"
    _description = "Field Trigger"

    old_value = fields.Char("Old Value")
    new_value = fields.Char("New Value")
    field_names = fields.Char("Field-Names")
    method = fields.Char(default="write")
    enabled = fields.Boolean(default=True)
    execute_at = fields.Selection(
        selection=[
            ("before.write", "Before Write"),
            ("after.write", "After Write"),
        ],
        default="before.write",
        required=True,
    )

    def _check_method(self):
        for rec in self:
            if rec.method != "write":
                rec.method = "write"
            super(FieldTrigger, rec)._check_method()

    def _get_fieldnames(self):
        fieldnames = (self.field_names or "").split(",")
        fieldnames = [fieldname.strip() for fieldname in fieldnames]
        return fieldnames

    @api.model
    def _update_registry(self):
        self.env["method_hook.trigger.mixin"]._update_registry()

    def _activate_hooks(self, patch, make_hook):
        for fieldtrigger in self.sudo().search([("enabled", "=", True)]):
            obj = self.env.get(fieldtrigger.model_id.model)
            execute_at = fieldtrigger.execute_at

            if not self._check_obj_exists(obj, fieldtrigger.model_id):
                continue

            def _on_write(recordset, method_name, args_packed):
                write_vals = args_packed["args"][0]
                current_trigger_is_filtered = args_packed.get("kwargs", {}).get(
                    "trigger.filters"
                )
                if current_trigger_is_filtered != execute_at:
                    return
                new_fieldtrigger = fieldtrigger.with_env(recordset.env).sudo()
                new_fieldtrigger._trigger_prepare(
                    recordset,
                    args_packed,
                    lambda linkedrecord: new_fieldtrigger._handle_write_event(
                        linkedrecord, write_vals, args_packed
                    ),
                )

            method = "write"
            patch(
                obj,
                method,
                make_hook(
                    self._name,
                    obj,
                    fieldtrigger.model_id.id,
                    method,
                    _on_write,
                    filters={
                        "event": fieldtrigger.execute_at,
                        "fieldname": fieldtrigger._get_fieldnames(),
                    },
                ),
                fieldtrigger.id,
            )

    def _handle_write_event(self, recordset, write_vals, args_packed):
        trigger = []

        for fieldname in self.field_names.split(","):
            fieldname = fieldname.strip()
            objfield = recordset._fields[fieldname]
            if objfield.compute and not objfield.inverse:
                raise ValidationError(
                    _("Computed field %(fieldname)s cannot be observed by datapolice.")
                    % locals()
                )
            if fieldname not in write_vals:
                continue
            if not self.old_value and not self.new_value:
                trigger.append((fieldname, write_vals[fieldname]))

            if self.old_value and self.new_value:
                if self._match_write_value(
                    fieldname,
                    self.old_value,
                    recordset[fieldname],
                    args_packed,
                ):
                    matches_new_value = self._match_write_value(
                        fieldname, self.new_value, write_vals[fieldname], args_packed
                    )
                    if matches_new_value:
                        trigger += matches_new_value

            elif self.old_value:
                trigger += self._match_write_value(
                    fieldname,
                    self.old_value,
                    recordset[fieldname],
                    args_packed,
                )
            elif self.new_value:
                trigger += self._match_write_value(
                    fieldname,
                    self.new_value,
                    write_vals[fieldname],
                    args_packed,
                )

        if trigger:
            self._trigger(recordset, args_packed, "write")

    @api.model
    def _value_match(self, val1, val2):
        if val1 == val2:
            return True
        if str(val1) == str(val2):
            return True
        try:
            if float(val1) == float(val2):
                return True
        except Exception:
            if int(val1) == int(val2):
                return True
        return False

    def _match_write_value(self, fieldname, value_as_char, write_value, args_packed):
        result = []
        if isinstance(write_value, models.BaseModel):
            if write_value:
                write_value = write_value.ids
        else:
            write_value = [write_value]
        for write_value in write_value:
            for value_as_char in value_as_char.split(","):
                value_as_char = value_as_char.strip()
                if not value_as_char:
                    continue
                if value_as_char.upper() == "FALSE":
                    value_as_char = False
                elif value_as_char.upper() == "TRUE":
                    value_as_char = True
                else:
                    try:
                        value_as_char = float(value_as_char)
                    except:
                        try:
                            value_as_char = int(value_as_char)
                        except:
                            pass

                if self._value_match(value_as_char, write_value):
                    result.append((fieldname, args_packed))
        return result
