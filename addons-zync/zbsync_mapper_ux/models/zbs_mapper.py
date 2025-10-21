# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
import uuid
from odoo import api, fields, models, SUPERUSER_ID, registry
from odoo.tools.safe_eval import safe_eval
import logging

logger = logging.getLogger(__name__)


class Mapper(models.Model):
    _inherit = "zbs.mapper"

    ux_input_sample = fields.Text("Input Sample")
    ux_input_sample_error = fields.Text("Input Sample Error", readonly=True)
    ux_input_path = fields.Char("Input Path")
    ux_input_mapped = fields.Text(compute="_compute_ux_input_mapped")
    ux_output_mapped = fields.Text(compute="_compute_ux_output_mapped")
    ux_preview = fields.Text(compute="compute_ux_preview")
    ux_version = fields.Integer()  # just a trigger

    @api.depends("ux_input_sample", "ux_version")
    def compute_ux_preview(self):
        for rec in self:
            mapped = {}
            try:
                db_registry = registry(self.env.cr.dbname)
                with db_registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    rec2 = rec.with_env(env)
                    record = json.loads(rec2.ux_input_sample or "{}")
                    record = self.env["zebrooset"].rs(record)
                    instance_env = {}
                    for mapping in rec2.root_mapping_ids():
                        mapping.with_context(
                            zbs_current_mapper=self, instance_env=instance_env
                        ).apply(record, mapped)
                rec.ux_preview = json.dumps(mapped, indent=4)
            except Exception as ex:
                rec.ux_preview = str(ex)
        return rec.ux_preview

    @api.constrains("ux_input_sample")
    def _format_input_sample(self):
        for rec in self:
            rec.ux_input_sample_error = ""
            try:
                d = json.loads(rec.ux_input_sample)
                d = json.dumps(d, indent=4)
                if d != rec.ux_input_sample:
                    rec.ux_input_sample = d
            except Exception as ex:
                rec.ux_input_sample_error = str(ex)

    def _compute_ux_output_mapped(self):

        def append_submappings(mapping, parent, all_mappings):
            mapdata = {
                "id": mapping.id,
                "field_source": mapping.field_source,
                "field_dest": mapping.field_dest,
                "action": mapping.action,
                "sequence": mapping.sequence,
                "children": [],
            }
            yield mapdata

            children = all_mappings.filtered(lambda x: x.parent_id == mapping)
            for child in children:
                children = list(append_submappings(child, mapping, all_mappings))
                mapdata["children"] += children

        for rec in self:
            res = {"source_fields": []}
            all_mappings = rec.mapping_ids
            for mapping in all_mappings.filtered(lambda x: not x.parent_id):
                res["source_fields"] += list(
                    append_submappings(mapping, None, all_mappings)
                )

            rec.ux_output_mapped = json.dumps(res, indent=4)

    @api.model
    def _get_fieldtype(self, value):
        try:
            pt = value._as_python_object()
        except:
            pt = None

        if pt and isinstance(pt, list):
            return "list"
        elif pt and isinstance(pt, dict):
            return "object"
        else:
            return "simple"

    def _analyze_field(
        self, record, parent_record, parent_key, current_path, parent_id
    ):
        res = []
        RS = self.env["zebrooset"].rs({})
        for key in record.keys():
            sample = record[key]
            ttype = self._get_fieldtype(sample)

            def _get_path():
                return ".".join(filter(bool, (parent_key or "").split(".") + [key]))

            path = _get_path()

            fielddata = {
                "id": str(uuid.uuid4()),
                "mapper_id": self.id,
                "name": key,
                "sample": sample,
                "type": ttype,
                "children": [],
                "path": path,
                "collapsed": True,
                "parent": ".".join(path.split(".")[:-1]),
                "parent_id": parent_id or None,
            }
            if not fielddata["parent"]:
                fielddata["parent"] = None

            res.append(fielddata)
            if ttype == "list":
                for idx, subrec in sample._iterate_records():
                    if not RS._is_scalar(subrec) and not subrec is None:
                        fielddata["children"] += self._analyze_field(
                            subrec,
                            record,
                            key,
                            path,
                            fielddata["id"],
                        )
                        break
            elif ttype == "object":
                for subfield in sample.keys():
                    fielddata["children"] += self._analyze_field(
                        sample,
                        record,
                        key,
                        path,
                        fielddata["id"],
                    )
                    break

            fielddata["lenchildren"] = len(fielddata["children"])
        return res

    @api.depends("ux_input_sample", "ux_input_path")
    def _compute_ux_input_mapped(self):
        for mapper in self:
            data = {"source_fields": []}

            mapper.ux_input_mapped = json.dumps(data)
            try:
                source = json.loads(mapper.ux_input_sample or "{}")
            except:
                try:
                    source = safe_eval(mapper.ux_input_sample or "[]")
                except Exception as ex:
                    logger.error(ex)
                    mapper.ux_input_sample_error = str(ex)
                    continue

            source = self.env["zebrooset"].rs(source)
            if mapper.ux_input_path:
                try:
                    source = self.env["zbs.tools"]._exec_get_result(
                        mapper.ux_input_path, {"record": source}
                    )
                except Exception as ex:
                    logger.error(ex)
                    mapper.ux_input_sample_error = str(ex)
                    continue

            try:
                for idx, rec in source._iterate_records():
                    data["source_fields"] = self._analyze_field(
                        rec, None, None, None, None
                    )
                    break
            except Exception as ex:
                logger.error(ex)
                mapper.ux_input_sample_error = str(ex)
                continue

            mapper.ux_input_mapped = self.env["zebrooset"].rs(data)._dumps()
            continue
