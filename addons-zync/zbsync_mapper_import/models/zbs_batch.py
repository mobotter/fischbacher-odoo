# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, fields, api
import json
from odoo.addons.zbsync.models.zebrooset import ZebrooSet
from odoo.exceptions import UserError


class ZbsWorker(models.Model):
    _inherit = "zbs.instance.line.batch"

    mapping_json = fields.Text("Output Json for Mapper")

    @api.constrains("output_data")
    def autogenerate_json(self):
        if self.find_next_mapper:
            try:
                self.generate_mapping_json()
            except Exception:
                pass

    def generate_mapping_json(self):
        for rec in self:
            rec.mapping_json = self._format_output(rec.output_data)

    @api.model
    def _format_output(self, data):
        try:
            formatted = self.env["zbs.pipeline.line"].load_data(data)
            if formatted and isinstance(formatted, ZebrooSet):
                if isinstance(formatted._as_python_object(), list):
                    formatted = formatted[0]
        except Exception as ex:
            raise UserError(
                "Output can not be formatted in a way the mapper can resolve Mappings. Please format data accordingly before copying"
            )
        else:
            try:
                formatted = json.dumps(formatted, indent=4)
            except:
                formatted = str(formatted)
            return formatted

    def copy_to_next_mapper(self):
        self.generate_mapping_json()
        instance = self.line_id.instance_id
        lineindex = instance.get_line_index(self.line_id)
        nl = instance.get_line_by_index(lineindex + 1)
        mapper = self.find_next_mapper(nl)
        if not mapper:
            raise UserError(
                f"No valid mapper was found for instance {instance.id}. Can not transfer found Data"
            )
        mapper.example_value = self.mapping_json
        mapper.example_value_type = "json"

    def find_next_mapper(self, line):
        instance = line.instance_id
        if line.original_line_id.worker_id._name == "zbs.mapper":
            return line.original_line_id.worker_id
        else:
            lineindex = instance.get_line_index(line)
            nl = instance.get_line_by_index(lineindex + 1)
            if not nl:
                return False
            return self.find_next_mapper(nl)
