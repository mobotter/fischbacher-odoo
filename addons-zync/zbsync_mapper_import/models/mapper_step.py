# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, fields
from odoo.exceptions import UserError
import json
import yaml


class ZbsMapper(models.Model):
    _inherit = "zbs.mapper"

    example_value = fields.Text("Example Value")
    example_value_type = fields.Selection(
        [("json", "json"), ("yaml", "yaml")],
        string="Specification Type",
        default="json",
    )

    def import_mappings(self):
        for rec in self:
            if not rec.example_value:
                raise UserError("No Example Data set. Please add a valid JSON or Yaml")
            else:
                try:
                    if rec.example_value_type == "json":
                        data = json.loads(rec.example_value)
                    elif rec.example_value_type == "yaml":
                        data = yaml.load(rec.example_value)
                    rec.generate_mappings(data)
                    rec.example_value = ""
                except Exception as e:
                    raise UserError(
                        f"Error while importing Mappings. Please make sure you put in a valid {rec.example_value_type}! Error thrown was {e}"
                    ) from e

    def generate_mappings(self, data, parent_id=False):
        mapcreate = self.env["zbs.mapping"]
        if not data or not isinstance(data, dict):
            return self
        else:
            for key, value in data.items():
                pa = parent_id.id if parent_id else False
                if self.env["zbs.mapping"].search(
                    [
                        ("step_id", "=", self.id),
                        ("field_source", "=", key),
                        ("field_dest", "=", key),
                        ("parent_id", "=", pa),
                    ]
                ):
                    continue
                if isinstance(value, dict) or isinstance(value, list):
                    t = mapcreate.create(
                        {
                            "force_name": (
                                f"{parent_id.force_name}-{key}" if parent_id else key
                            ),
                            "action": "object" if isinstance(value, dict) else "list",
                            "field_source": key,
                            "field_dest": key,
                            "parent_id": pa,
                        }
                    )
                    self.mapping_ids = [(4, t.id)]
                    if isinstance(value, list):
                        v = mapcreate.create(
                            {
                                "force_name": (
                                    f"{parent_id.force_name}-{key}-ITEM"
                                    if parent_id
                                    else key
                                ),
                                "action": "object",
                                "field_source": "",
                                "field_dest": "",
                                "parent_id": t.id if t else False,
                            }
                        )
                        for val in value:
                            self.generate_mappings(val, v)
                    else:
                        self.generate_mappings(value, t)
                else:
                    t = mapcreate.create(
                        {
                            "force_name": (
                                f"{parent_id.force_name}-{key}" if parent_id else key
                            ),
                            "action": "direct",
                            "field_source": key,
                            "field_dest": key,
                            "parent_id": pa,
                        }
                    )
                    self.mapping_ids = [(4, t.id)]
        return self
