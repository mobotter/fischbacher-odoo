# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, fields, api
from odoo.exceptions import UserError
import json


class ZbsyncTransformer(models.Model):
    _inherit = ["zbs.transformer", "zbs.xport.mixin"]
    _name = "zbs.transformer.edi"
    _description = "Zync EDI Transformer"

    direction = fields.Selection([("out", "out"), ("in", "in")], default="in")
    input_type = fields.Selection(
        [("byte", "byte"), ("raw", "raw"), ("string", "string")], default="byte"
    )
    edi_mapping_line_ids = fields.One2many(
        "zbs.edi.mapping.line",
        "edi_transformer_id",
        string="Edi Mapping Lines",
        copy=True,
    )
    edi_mappings_ids = fields.One2many(
        "zbs.edi.mapping",
        "edi_transformer_id",
        string="Edi Mappings",
        compute="_compute_mappings",
        store=True,
        copy=True,
    )
    header_line = fields.Char("Header Line")
    line_break_char = fields.Selection(
        [("newline", "New Line"), (";", "Semicolon"), (",", "Colon")]
    )
    line_start = fields.Selection(
        [("number", "Line Number"), ("start_code", "Start Code")]
    )
    field_split_type = fields.Selection(
        [("field_length", "Field Length"), ("break_char", "Break Char")]
    )
    line_split_char = fields.Char("Line Split Char")
    export_file_name = fields.Char("File Name")
    edi_example_type = fields.Selection(
        [("edi", "Edi"), ("mapping_json", "Mapping Json")], default="edi"
    )
    edi_example = fields.Text("EDI Import Values")

    def parse_example(self):
        if self.edi_example_type == "edi":
            raise NotImplementedError()
        elif self.edi_example_type == "mapping_json":
            data = False
            try:
                data = json.loads(self.edi_example)
            except:
                raise Exception(
                    f"Error while loading EDI Mapping Json. Please make sure the data you input is in valid JSON Format {self.edi_example}"
                )
            for val in data:
                mapping_line = {}
                t = self.env["zbs.edi.mapping.line"].search(
                    [
                        ("action_type", "=", val["action_type"]),
                        ("line_number", "=", val["line_number"]),
                        ("name", "=", val["name"]),
                        ("start_code", "=", val["start_code"]),
                    ]
                )
                if not t:
                    for key in val:
                        if key in ["zync_uuid", "__record_id"]:
                            continue
                        mapping_line[key] = val[key]
                    mapping_line["edi_transformer_id"] = self.id

                    t = self.env["zbs.edi.mapping.line"].create(mapping_line)
                    for mapping in val["edi_mapping_line_ids"]:
                        newmapping = {}
                        v = self.env["zbs.edi.mapping.line"].search(
                            [
                                ("field_count", "=", mapping["field_count"]),
                                ("field_length", "=", mapping["field_length"]),
                                ("field_name", "=", mapping["field_name"]),
                                ("field_start", "=", mapping["field_start"]),
                                (
                                    "edi_transformer_id",
                                    "=",
                                    mapping["edi_transformer_id"],
                                ),
                            ]
                        )
                        if not v:
                            for key in mapping:
                                if key in ["zync_uuid", "__record_id"]:
                                    continue
                                newmapping[key] = mapping[key]
                            newmapping["edi_transformer_line_id"] = t.id
                            self.env["zbs.edi.mapping.line"].create(newmapping)

    @api.depends("edi_mapping_line_ids")
    def _compute_mappings(self):
        for rec in self:
            mappings = []
            for mapping_line in rec.edi_mapping_line_ids:
                for mapping in mapping_line.edi_mapping_ids:
                    if mapping.id not in mappings:
                        mappings.append(mapping.id)
            addmapps = rec.env["zbs.edi.mapping"].search(
                [("edi_transformer_id", "=", rec.id)]
            )
            for map in addmapps:
                if map.id not in mappings:
                    mappings.append(map.id)
            rec.edi_mappings_ids = [[6, 0, mappings]]

    def process(self, instance, data, errors=None):
        val = False
        if errors:
            data["content"] = errors
        func = getattr(self, "_" + self.direction, None)
        val = func(data)
        data = super().process(instance, val)
        return data

    def _in(self, data):
        val = {}
        content = False
        if self.input_type == "byte":
            if not data["content"]:
                raise UserError(
                    "Please make sure the data has a string Content Field before starting Transformer"
                )
            try:
                content = data["content"].encode("utf-8")
            except Exception:
                raise UserError(
                    "There was a problem when transforming the input data. is the input a byte-string like it is specified?"
                )
        elif self.input_type == "raw":
            content = data["content"]
        elif self.input_type == "string":
            content = data
        else:
            raise NotImplementedError()
        t = self.line_break_char
        if self.line_break_char == "newline":
            t = "\n"
        lines = content.split(t)
        for mapline in self.edi_mapping_line_ids.filtered(
            lambda x: x.parent_id.id == False
        ):
            val[mapline.name] = mapline.parse_mappings(lines)
        return val

    def _out(self, data):
        self.check_plausibility(data)
        t = self.line_break_char
        if self.line_break_char == "newline":
            t = "\n"

        edistring = self.header_line + t if self.header_line else ""
        vals = []
        i = 0
        for d in data:
            all_mapping_lines = self.edi_mapping_line_ids.filtered(
                lambda x: x.parent_id.id == False
            ).sorted(key=lambda r: (r.line_number))

            for mapline in all_mapping_lines:
                edistring = mapline.write_edi_string(d, edistring)
            filename = self._eval_file_name(i, d, data)
            result = {"content": edistring, "filename": filename}
            i = i + 1
            vals.append(result)

        return vals

    def check_plausibility(self, data):
        for d in data:
            d = d._d
            dstring = json.dumps(d, indent="4")
            if isinstance(d, dict):
                for key in d:
                    if isinstance(d[key], dict):
                        for subkey in d[key]:
                            if isinstance(d[key][subkey], dict) or isinstance(
                                d[key][subkey], list
                            ):
                                raise UserWarning(
                                    f"Input Value is not properly set up! Please restrict Value to 2 Levels of object depth while mapping! Input data\n{dstring}"
                                )
                    if isinstance(d[key], list):
                        for entry in d[key]:
                            if isinstance(entry, dict):
                                for subkey in entry:
                                    if isinstance(entry[subkey], dict) or isinstance(
                                        entry[subkey], list
                                    ):
                                        raise UserWarning(
                                            f"Input Value is not properly set up! Please restrict Value to 2 Levels of object depth while mapping! Input data\n{dstring}"
                                        )
            else:
                raise UserWarning(
                    f"Input Value not properly set up! You are putting in a not a dictornary which is not supported! Input data\n{dstring}"
                )

    def _do_exec(self, record, data, index, instance, errors=False):
        return data

    def _eval_file_name(self, index, record, data):
        self.ensure_one()
        name = (self.export_file_name or "").strip()
        instance = self.env.context.get("zbs_instance")
        _globals = instance._get_default_objects(
            {
                "index": index,
                "record": record,
                "input": data,
            }
        )
        if len(name.splitlines()) <= 1:
            name = 'f"' + name + '"'
            name = self.env["zbs.tools"]._exec_get_result(name, _globals)
        else:
            name = self.env["zbs.tools"]._exec_get_result(name, _globals)
        return name


class ZbsyncEdiMappings(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.edi.mapping.line"
    _description = "Zync EDI Mapping"
    _order = "line_number, start_code"

    name = fields.Char(
        string="Name", compute="_compute_display_name", store=True, compute_sudo=True
    )
    display_name = fields.Char(compute_sudo=True)
    force_name = fields.Char(string="Force Name")
    source_location = fields.Char(string="Source Location")
    edi_transformer_id = fields.Many2one(
        "zbs.transformer.edi",
        string="Edi Transformer",
        xport_ignore=True,
    )
    action_type = fields.Selection(
        [("direct", "direct"), ("list", "list"), ("object", "object")], default="direct"
    )

    start_code = fields.Char("Start Code")
    line_number = fields.Integer("Line Number")

    line_break_char = fields.Selection(
        related="edi_transformer_id.line_break_char", store=True
    )
    line_start = fields.Selection(related="edi_transformer_id.line_start", store=True)
    field_split_type = fields.Selection(
        related="edi_transformer_id.field_split_type", store=True
    )
    line_split_char = fields.Char(
        related="edi_transformer_id.line_split_char", store=True
    )
    edi_mapping_ids = fields.One2many(
        "zbs.edi.mapping",
        "edi_mapping_line_id",
        string="Edi Mappings",
        copy=True,
    )
    parent_id = fields.Many2one(
        "zbs.edi.mapping.line",
        string="Parent",
        help="Shows that a Mapping Line belongs to anther line. this line will be printed AFTER the parent line."
        "If a parent has multiple children, they are printed in  line sequence.",
    )
    child_ids = fields.One2many(
        comodel_name="zbs.edi.mapping.line",
        inverse_name="parent_id",
        string="Children",
        compute="_compute_children",
        store=True,
        copy=True,
    )

    @api.depends("force_name", "start_code", "action_type")
    def _compute_name(self):
        for rec in self:
            rec.name = (
                rec.force_name
                if rec.force_name
                else f"Line {rec.start_code} {rec.action_type}"
            )

    @api.depends(
        "edi_transformer_id.edi_mapping_line_ids",
        "edi_transformer_id.edi_mapping_line_ids.parent_id",
    )
    def _compute_children(self):
        for rec in self:
            children = rec.edi_transformer_id.edi_mapping_line_ids.filtered(
                lambda x: x.parent_id == rec.id
            )
            if children:
                rec.child_ids = [[6, 0, children.ids]]
            # else:
            #    rec.child_ids = False

    def write_edi_string(self, d, edistring):
        t = "\n" if self.line_break_char == "newline" else self.line_break_char
        split_char = self.line_split_char
        mps = self.edi_mapping_ids.sorted(key=lambda r: (r.field_count))
        if self.source_location:
            try:
                d = d[self.source_location]
            except:
                raise UserError(
                    f"Error while parsing source location. Location {self.source_location}, data"
                )
        if self.action_type == "list":
            for listentry in d:
                edistring += self.start_code
                edistring = self._write_edi_detail(
                    edistring, split_char, mps, listentry
                )
                edistring += t
                for child in self.child_ids:
                    edistring = child.write_edi_string(listentry, edistring)
        else:
            edistring += self.start_code
            edistring = self._write_edi_detail(edistring, split_char, mps, d)
            edistring += t
            for child in self.child_ids:
                edistring = child.write_edi_string(d, edistring)
        return edistring

    def _write_edi_detail(self, edistring, split_char, mps, d):
        if self.field_split_type == "break_char" and min(mps.mapped("field_count")) > 1:
            cnt = min(mps.mapped("field_count")) - 1
            j = 1
            while j < cnt:
                edistring += split_char
                j = j + 1
        for i, mapping in enumerate(mps):
            if i + 1 == len(mps):
                split_char = ""
            edistring = mapping.write_mapping(edistring, d, split_char)
        return edistring

    def parse_mappings(self, alllines):
        mps = self.edi_mapping_ids.sorted(key=lambda r: (r.field_count))
        if not alllines:
            return False
        if self.action_type == "direct" or self.action_type == "object":
            result = {}
            line = self._find_relevant_lines(alllines)[0]
            result = self.get_line_val(mps, line, result)
            for child in self.child_ids:
                relevant_lines = child._find_relevant_lines(alllines)
                result[child.name] = child.parse_mappings(relevant_lines)
            return result
        elif self.action_type == "list":
            lines = self._find_relevant_lines(alllines)
            results = []
            i = 0
            for line in lines:
                result = {}
                result = self.get_line_val(mps, line, result)
                for child in self.child_ids:
                    relevant_lines = child._find_relevant_lines(alllines)
                    result[child.name] = child.parse_mappings(relevant_lines)
                result["index"] = i
                i = i + 1
                results.append(result)
            return results
        else:
            raise NotImplementedError("Not Implemented")

    def get_line_val(self, mappings, line, result):
        try:
            for mapping in mappings:
                if self.field_split_type == "field_length":
                    result[mapping.field_name] = line[
                        mapping.field_start : mapping.field_start + mapping.field_length
                    ]
                if self.field_split_type == "break_char":
                    line_fields = line.split(self.line_split_char)
                    result[mapping.field_name] = line_fields[mapping.field_count - 1]
        except Exception as e:
            raise Exception(
                f"Error while finding the lineval for {mapping.display_name} Line Fields: {line_fields} - the Error was: {e}"
            )
        return result

    def open_line(self):
        return {
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "type": "ir.actions.act_window",
            "context": {},
            "target": "new",
        }

    def _find_relevant_lines(self, lines):
        relevant_lines = []
        if self.line_start == "number":
            relevant_lines.append(lines[self.line_number].strip())
        elif self.line_start == "start_code":
            for line in lines:
                line = line.strip()
                if line.startswith(self.start_code):
                    relevant_lines.append(line)
        return relevant_lines


class ZbsyncEdiMappings(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.edi.mapping"
    _description = "Zync EDI Mapping"
    _order = "line_number, start_code"

    name = fields.Char(
        string="Name", compute="_compute_display_name", store=True, compute_sudo=True
    )
    display_name = fields.Char(compute_sudo=True)
    edi_mapping_line_id = fields.Many2one(
        "zbs.edi.mapping.line",
        string="Edi Mapping Line",
        xport_ignore=True,
    )
    edi_transformer_id = fields.Many2one(
        "zbs.transformer.edi",
        string="Edi Transformer",
        xport_ignore=True,
    )
    line_number = fields.Integer(related="edi_mapping_line_id.line_number", store=True)
    start_code = fields.Char(related="edi_mapping_line_id.start_code", store=True)
    line_break_char = fields.Selection(
        related="edi_mapping_line_id.line_break_char", store=True
    )
    line_start = fields.Selection(related="edi_transformer_id.line_start", store=True)
    field_split_type = fields.Selection(
        related="edi_mapping_line_id.field_split_type", store=True
    )
    line_split_char = fields.Char(
        related="edi_mapping_line_id.line_split_char", store=True
    )
    field_name = fields.Char("Field Name", required=True)
    field_count = fields.Integer("Field Index")
    field_start = fields.Integer("Field Start")
    field_length = fields.Integer("Field Length")

    @api.depends("field_name")
    def _compute_display_name(self):
        res = []
        for rec in self:
            if not rec.exists():
                rec.display_name = "Deleted"
            else:
                name = rec.field_name if rec.field_name else f"{rec.field_count}"
                rec.display_name = name
                rec.name = name

    def write_mapping(self, edistring, data, splitchar):

        if self.field_name and self.field_name not in data:
            return (edistring or "") + (splitchar or "")
        value = str(data[self.field_name]) if data[self.field_name] else ""
        if self.field_length:
            value = value[: self.field_length]
        if splitchar:
            edistring = f"{edistring}{value}{splitchar}"
        else:
            edistring = f"{edistring}{value}"
        return edistring

    def create(self, vals):
        if "name" in vals and "field_name" not in vals:
            vals["field_name"] = vals["name"]
        result = super().create(vals)
        return result

    def open_mapping(self):
        return {
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "type": "ir.actions.act_window",
            "context": {},
            "target": "new",
        }
