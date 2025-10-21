# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.addons.zbsync.models.zebrooset import _WrappedList
from odoo.addons.zbsync.exceptions import SkipRecord


class FieldMissingException(Exception):
    pass


class Mapping(models.Model):
    _inherit = ["zbs.xport.mixin", "mail.thread"]
    _name = "zbs.mapping"
    _description = "Zync Mapping"
    _order = "sequence"
    _parent_name = "parent_id"
    _parent_store = True

    lookup_use_cache = fields.Boolean(
        "Use Cache (Alpha Implementation)",
        default=False,
        help="ALPHA IMPLEMENTATION!; Cache is reset at process start.",
    )
    current_mapper = fields.Many2one(
        "zbs.mapper", compute="_compute_mapper", search="_search_mapper"
    )
    no_metadata = fields.Boolean(related="current_mapper.no_metadata", store=False)

    name = fields.Char(compute="_compute_name", store=True)
    force_name = fields.Char("Force Name", tracking=True)
    active = fields.Boolean("Active", default=True, tracking=True)
    sequence = fields.Integer(default=9999, tracking=True)
    parent_path = fields.Char(index="btree", xport_ignore=True)
    child_ids = fields.One2many(
        "zbs.mapping", "parent_id", string="Children", copy=False
    )
    may_miss = fields.Boolean("Source may miss", tracking=True)
    skip_if_empty = fields.Boolean("Skip if mapped value empty", tracking=True)
    unlink_subrecords = fields.Boolean("Unlink Subrecords", tracking=True)
    filter_to_delta = fields.Boolean("Filter Delta", default=False, tracking=True)
    no_create = fields.Boolean("No Create (only for dumping in Odoo)", tracking=True)
    no_update = fields.Boolean("No Update (only for dumping in Odoo)", tracking=True)
    default_value = fields.Boolean(
        "Default Value", help="Only set at write if False on other side", tracking=True
    )
    # TODO implement
    filter_domain = fields.Char(
        "Filter Domain",
        help="e.g. record.name.startswith('a') or record.field in [1,2,3]",
        tracking=True,
    )
    # TODO quickformats
    pyfunc_id = fields.Many2one("zbs.mapping.pyfunc", string="Function", tracking=True)
    skip_record_expr = fields.Text("Expression to skip whole record", tracking=True)
    loop_records = fields.Boolean("Loop Records")
    action = fields.Selection(
        [
            ("direct", "=>"),
            ("object", "{}"),
            ("list", "[]"),
            ("eval", "code"),
            ("eval_default", "default"),
            ("mapped_values", "Value Mappings"),
            ("lookup", "Lookup"),  # TODO implement that record is created if not found
            # TODO trurnit lookup auf many2many auch machen z.B. wenn komma getrennt
            # environment values: they can be grabbed from data; is collected by file grabbers then
        ],
        string="Action",
        required=True,
        default="direct",
        tracking=True,
    )
    format_value = fields.Text(
        "Format Expression", help="str(value).strip()", tracking=True
    )
    code = fields.Char("Code", tracking=True)
    field_source = fields.Char("Source Field", tracking=True)
    field_dest = fields.Char("Destination Field", tracking=True)
    parent_id = fields.Many2one(
        "zbs.mapping",
        string="Parent",
        index=True,
        ondelete="cascade",
        xport_ignore=True,
        tracking=True,
        copy=False,
    )
    step_id = fields.Many2one(
        "zbs.mapper", string="Step", xport_ignore=True, tracking=True
    )
    is_key = fields.Boolean("Is Key", tracking=True)
    level = fields.Integer("Level", tracking=True)
    hierarchy_indicator = fields.Char(
        "Hierarchy Indicator",
        compute="_compute_hierarchy_indicator",
        store=True,
        tracking=True,
    )
    comment = fields.Text("Comment", tracking=True)
    mapped_value_ids = fields.One2many(
        "zbs.mapping.mapvalues", "mapper_id", string="Mapped Values", tracking=True
    )
    strict_mapped_types = fields.Boolean("Strict Mapped Types", tracking=True)
    lookup_action_on_no_match = fields.Selection(
        [
            ("create", "Create"),
            ("raise_error", "Raise Error"),
        ],
        default="",
        string="Action if not found",
    )
    lookup_model = fields.Char("Lookup Model", tracking=True)
    lookup_field = fields.Char("Lookup Field", tracking=True)
    lookup_operator = fields.Selection(
        [("=", "="), ("ilike", "ilike"), ("like", "like")],
        string="Lookup Operator",
        default="ilike",
        tracking=True,
    )
    skip_if = fields.Selection(
        [
            ("never", "Never"),
            (
                "not_in_envs",
                "If not in env.fields",
            ),  # trigger method hook puts changed fields into 'fields'
        ],
        tracking=True,
    )
    output_stream = fields.Selection([("env", "Environment")], tracking=True)
    possible_parent_mapping_ids = fields.Many2many(
        "zbs.mapping", compute="_compute_possible_parent_mappings"
    )

    @api.depends_context("mapper_id")
    def _compute_possible_parent_mappings(self):
        for rec in self:
            mappings = self.env["zbs.mapping"]
            if self.env.context.get("mapper_id"):
                mapper = self.env["zbs.mapper"].browse(
                    self.env.context.get("mapper_id")
                )
                mappings = mapper.mapping_ids
            rec.possible_parent_mapping_ids = mappings

    def open_mapping(self):
        return {
            "name": _("Mapping"),
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "context": self.env.context,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def open_mapvalues(self):
        return {
            "name": _("Mapped Values"),
            "view_type": "form",
            "res_model": self.mapped_value_ids._name,
            "context": {
                "default_mapper_id": self.id,
            },
            "domain": [("mapper_id", "=", self.id)],
            "views": [(False, "tree")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    @api.constrains("parent_id")
    def _recalc_level_struct(self):
        roots = set()
        for rec in self:
            roots.add(rec.root)
        for root in roots:
            for el, level in root._traverse():
                el.level = level

    def _traverse(self, level=0):
        yield (self, level)
        for child in self.active_child_ids:
            yield from child._traverse(level + 1)

    @property
    def root(self):
        p = self
        while p.parent_id:
            p = p.parent_id
        return p

    def _compute_level(self):
        for rec in self:
            level = 0
            p = rec
            while p:
                p = p.parent_id
                level += 1
            rec.level = level - 1

    @api.depends("level")
    def _compute_hierarchy_indicator(self):
        for rec in self:
            rec._compute_level()
            if rec.level == 1:
                rec.hierarchy_indicator = "-"
            else:
                rec.hierarchy_indicator = "----" * (rec.level)

    @api.depends("field_dest", "field_source", "force_name")
    def _compute_name(self):
        for rec in self:
            if rec.force_name:
                rec.name = rec.force_name
            else:
                if not rec.field_source and not rec.field_dest:
                    rec.name = f"#{rec.id}"
                else:
                    rec.name = (
                        f"{rec.id}#{rec.field_source or ''} => {rec.field_dest or ''}"
                    )

    @api.model
    def _get_source_value(self, record, field):
        value = None
        try:
            if not record and self.may_miss:
                return value

            # no dunder allowed mmphf
            def convert(x):
                if isinstance(x, str):
                    if "[" in x:
                        return x

                return f"['{x}']"

            if not field and self.action not in ["list", "object"]:
                raise ValidationError(f"Missing field for mapping #{self.id}")

            if "." in field:
                parts = "." + field
            else:
                parts = "".join(map(convert, field.split(".")))
            source_value = None
            if field:
                if "$value" not in field:
                    # This is a problem Imho. this try else does not result in the FieldMissing to be triggered
                    try:
                        source_value = record[field]
                    except Exception as ex:
                        source_value = record

            if "$value" in field:
                value = str(record)
            else:
                value = self.env["zbs.tools"]._exec_get_result(
                    f"record{parts}", {"record": record, "value": source_value}
                )
        except (AttributeError, KeyError, ValueError) as ex:
            raise FieldMissingException(field) from ex
        except Exception as ex:
            raise Exception(f"Error at mapping: {self.id}") from ex
        else:
            if self.format_value:
                try:
                    value = self.env["zbs.tools"]._exec_get_result(
                        self.format_value, {"value": value}
                    )
                except Exception as ex:
                    raise ValidationError(f"Error at mapping #{self.id}: {ex}") from ex
        return value

    def apply(self, record, mapped):

        self.ensure_one()

        if self.skip_if == "not_in_envs" and self.field_source:
            try:
                env_fields = self.env.context["zbs_instance_env"].fields
            except KeyError:
                pass
            else:
                if self.field_source not in env_fields:
                    return

        if (self.skip_record_expr or "").strip():
            if self.field_source:
                value = self._get_source_value(record, self.field_source)
            else:
                value = record
            if self.env["zbs.tools"]._exec_get_result(
                self.skip_record_expr,
                {"record": record, "mapped": mapped, "value": value, "env": self.env},
            ):
                raise SkipRecord

        try:
            if self.action in ["direct"]:
                value = self._get_source_value(record, self.field_source)
                self._set_value(mapped, value)
            elif self.action in ["lookup"]:
                value = self._get_source_value(record, self.field_source)
                self._apply_lookup(value, mapped, record)

            elif self.action in ["object", "list"]:
                self._apply_object_list(record, mapped)
            elif self.action == "mapped_values":
                self._apply_mapped_values(record, mapped)
            elif self.action == "eval":
                self._apply_code(record, mapped)
            elif self.action == "eval_default":
                self._apply_code(record, mapped)

            else:
                raise NotImplementedError(self.action)
        except FieldMissingException as ex:
            if not self.may_miss:
                raise UserError(
                    f"(Mapping#{self.id}) Field was not found in source! Field:{self.field_source}, record:{record}"
                ) from ex

        def default_list(name, value):
            if name not in mapped:
                mapped[name] = []
            if value not in mapped[name]:
                mapped[name].append(value)

        if isinstance(mapped, dict):
            if self.skip_if_empty and self.field_dest in mapped:
                # TODO Boolean vs. is NONE
                if not mapped[self.field_dest]:
                    mapped.pop(self.field_dest)

        if not self.no_metadata:
            if self.filter_to_delta and isinstance(mapped, dict):
                mapped["___filter_to_delta"] = True
            if self.no_create:
                mapped["___no_create"] = True
            if self.no_update:
                mapped["___no_update"] = True

            current_mapper = self.env.context.get("current_mapper")

            if self.is_key and current_mapper.can_keys:
                default_list("___keys", self.field_dest)

            if self.default_value:
                default_list("___default_values", self.field_dest)

            if self.unlink_subrecords:
                default_list("___keys_delete", self.field_dest)

    def _write_to_env(self, env_expression, value):
        self.env.context["zbs_instance_env"][env_expression] = value

    def _set_value(self, mapped, value, dest_field=None):
        dest_field = dest_field or self.field_dest
        if not dest_field:
            return
        if self.output_stream == "env":
            self._write_to_env(dest_field, value)
        else:
            mapped[dest_field] = value

    def _apply_lookup_search(self, model, field, operator, value):
        if self.lookup_use_cache:
            return self._apply_lookup_search_cached(model, field, operator, value)
        else:
            return self._apply_lookup_search_uncached(model, field, operator, value)

    @api.model
    @tools.ormcache("model", "field", "operator", "value")
    def _apply_lookup_search_cached(self, model, field, operator, value):
        return self._apply_lookup_search_uncached(model, field, operator, value)

    def _apply_lookup_search_uncached(self, model, field, operator, value):
        matches = self.env[model].search([(field, self.lookup_operator, value)])
        return matches

    def _apply_lookup(self, value, mapped, record):
        dest_field, model, field = self.field_dest, self.lookup_model, self.lookup_field
        if not model or not field:
            raise ValidationError("Please provide lookup-model and field!")
        if not value:
            self._set_value(mapped, False, dest_field)

        is_list = isinstance(value, (list, tuple))
        if not is_list:
            value = [value]
        res = []
        for _v in value:
            if not _v:
                res.append(None)
                continue
            matches = self._apply_lookup_search(model, field, self.lookup_operator, _v)
            if len(matches) > 1:
                raise ValidationError(
                    f"Mapping #{self.id}: Too many values found in {model} for {_v}"
                )
            if len(matches) == 1:
                res.append(matches[0].id)
            elif not matches:
                if self.lookup_action_on_no_match == "raise_error":
                    raise UserError(
                        f"Lookup-Record not found for: {field}{self.lookup_operator}{_v}"
                    )
                elif (
                    self.lookup_action_on_no_match == "create"
                    or not self.lookup_action_on_no_match
                ):
                    if not self.active_child_ids:
                        # create item in dumper
                        if not self.no_metadata:
                            res.append({field: _v, "___keys": [field]})
                    else:
                        self._apply_object_list(record, mapped, action="object")
                        res.append(mapped[self.field_dest])
                else:
                    raise NotImplementedError(self.lookup_action_on_no_match)

        if not is_list:
            res = res[0]
        self._set_value(mapped, res, dest_field=dest_field)

    def _apply_code(self, record, mapped):
        from odoo.addons.zbsync.exceptions import SkipRecord, ZBSPipelineException

        code = self.code or self.field_source
        value = None
        if self.field_source:
            try:
                value = self._get_source_value(record, self.field_source)
            except Exception:
                value = self.field_source  # seems to contain code
        try:
            res = self.env["zbs.tools"]._exec_get_result(
                code,
                {
                    "instance_env": self.env.context["zbs_instance_env"],
                    "instance": self.env.context.get("zbs_instance"),
                    "record": record,
                    "mapped": mapped,
                    "value": value,
                    "env": self.env,
                },
            )
        except (SkipRecord, ZBSPipelineException):
            raise
        except Exception as ex:
            raise ValueError(
                f"Mapping: #{self.id}: Error for evaluating {self.field_source or 'no field'}=>{self.field_dest}:\n{ex}"
            ) from ex
        if isinstance(mapped, list):
            mapped.append(res)
        else:
            self._set_value(mapped, res)

    @property
    def active_child_ids(self):
        return self.child_ids.filtered(lambda x: x.active)

    def _apply_object_list(self, record, mapped, action=None, errors=None):
        from odoo.addons.zbsync.exceptions import SkipRecord

        action = action or self.action
        object = self._apply_object_list_create_parent(action, mapped)

        def apply_child(child, item, object):
            try:
                child.apply(item, object)
            except SkipRecord:
                pass

        current_mapper = self.env.context.get("current_mapper")
        for child in self.active_child_ids:
            if self.loop_records:

                def on_record(instance, index, record, data, errors=None):
                    if self._is_list(object):
                        remember_len = len(object)

                    apply_child(child, record, object)

                    if self._is_list(object):
                        new_len = len(object)
                        assert new_len > remember_len
                        res = object[-(new_len - remember_len) :]
                    else:
                        res = object
                    return res

                current_mapper.get_records_for_apply(on_record)

            else:
                subset = record
                if self.field_source:
                    if self.action != "lookup":
                        subset = self._get_source_value(subset, self.field_source)
                if self.may_miss and not subset:
                    break
                if self._is_list(subset) and isinstance(object, list):
                    for item in subset:
                        apply_child(child, item, object)
                else:
                    apply_child(child, subset, object)
        return mapped

    def _apply_object_list_create_parent(self, action, mapped):
        if action == "object":
            if isinstance(mapped, list):
                mapped.append({})
                object = mapped[-1]
            else:
                if not self.field_dest:
                    object = mapped
                else:
                    self._set_value(mapped, {})
                    object = mapped[self.field_dest]
        elif action == "list":
            self._set_value(mapped, [])
            object = mapped[self.field_dest]
        else:
            raise NotImplementedError(action)
        return object

    def _is_list(self, obj):
        return isinstance(obj, (_WrappedList, list, models.Model))

    def _apply_mapped_values(self, record, mapped):
        source_value = self._get_source_value(record, self.field_source)
        if not source_value and self.skip_if_empty:
            return
        mapval = self.mapped_value_ids.filtered(lambda x: x._equals(source_value))
        if not mapval and not source_value:
            mapval = self.mapped_value_ids.filtered(lambda x: x.default_value)

        if not mapval:
            raise ValidationError(
                f"Value {source_value} not found in mapping {self.name} (#{self.id})"
            )
        if len(mapval) > 1:
            raise ValidationError(
                f"Value {source_value} found multiple times in "
                f"mapping {','.join(filter(bool, mapval.mapped('dest_value')))} "
                f"#{self.id}"
            )
        self._set_value(mapped, mapval.as_value(mapval.dest_value))

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("step_id"):
                if vals.get("parent_id"):
                    parent = self.browse(vals["parent_id"])
                    vals["step_id"] = parent.step_id.id
        res = super().create(vals_list)
        self._invalidate_mapping_cache()
        return res

    def ok(self):
        return True

    @api.depends_context("pipeline")
    def _compute_mapper(self):
        for rec in self:
            if self.env.context.get("zbs_current_mapper"):
                rec.current_mapper = self.env.context.get("zbs_current_mapper")
            else:
                pl = self.env.context.get("zbs_pipeline")
                if not pl:
                    rec.current_mapper = False
                    continue
                rec.current_mapper = pl.worker_id.id

    def _search_mapper(self, operator, value):
        if isinstance(value, list):
            assert all(isinstance(x, int) for x in value)
        res = self.env["zbs.mapper"].search([("id", operator, value)])
        return [("id", "in", res.ids)]

    def heartbeat(self):
        return self.step_id.heartbeat()

    @api.constrains("loop_records", "action")
    def _loop_records_constraint(self):
        for rec in self:
            if rec.action not in ["list", "object"]:
                if rec.loop_records:
                    raise ValidationError(
                        "Cannot set loop records if action is not list or object"
                    )

    def copy(self, default=None):
        if default is None:
            default = {}
        if self.env.context.get("default_step_id"):
            default["step_id"] = self.env.context["default_step_id"]
        res = super().copy(default)

        for child in self.active_child_ids:
            new_child = child.copy()
            new_child.parent_id = res
        return res

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_mapping_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self._invalidate_mapping_cache()
        return res

    @api.model
    def _invalidate_mapping_cache(self):
        obj = self.env[self._name]
        self.env["zbs.tools"].do_clear_cache(obj=obj)
