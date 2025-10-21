# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, models, fields
import json
import yaml
import xmltodict


class BackendModel(models.Model):
    _name = "zbs.backend.model"
    _description = "Zync Backend Model for Mappings"

    name = fields.Char("Name", required=True)
    error = fields.Boolean("Error")
    error_message = fields.Text("Parse Error")
    backend_value = fields.Text("Backend Value", help="Please add ")
    backend_value_type = fields.Selection(
        [("json", "json"), ("yaml", "yaml"), ("xml", "xml")],
        string="Specification Type",
        default="json",
    )
    group_id = fields.Many2one("zbs.backend.model.group")

    @api.constrains("backend_value", "backend_value_type")
    def _check_parse(self):
        try:
            self.get_data()
            self.error = False
            self.error_message = ""
        except Exception as e:
            self.error = True
            self.error_message = f"Error while parsing data. Error Message : {e}"

    def get_data(self):
        try:
            func = getattr(self, "_" + self.backend_value_type, None)
            return func()
        except Exception as e:
            self.error = True
            self.error_message = f"Error while parsing data. Error Message : {e}"
            return []

    def _json(self):
        if not self.backend_value_type:
            raise Exception("No Value for Backend Model provided")
        return json.loads(self.backend_value)

    def _yaml(self):
        if not self.backend_value_type:
            raise Exception("No Value for Backend Model provided")
        return yaml.load(self.backend_value_type)

    def _xml(self):
        if not self.backend_value_type:
            raise Exception("No Value for Backend Model provided")
        return xmltodict.parse(self.backend_value)


class BackendModelGroup(models.Model):
    _name = "zbs.backend.model.group"
    _description = "ZBS Method for aggregation backend models"

    name = fields.Char("Name")


#     field_ids = fields.One2Many(
#         "zbs.backend.model", "backend_model_id", string="Fields"
#     )


#     def import_fields(self):
#         for rec in self:
#             if not rec.example_value:
#                 raise UserWarning("No Example Data set. Please add a valid JSON or Yaml")
#             else:
#                 try:
#                     if rec.example_value_type == 'json':
#                         data = json.loads(rec.example_value)
#                     elif rec.example_value_type == 'yaml':
#                         data = yaml.load(rec.example_value)
#                     rec.generate_fields(data)
#                 except Exception as e:
#                     raise UserWarning(f"Error while importing Fields. Please make sure you put in a valid {rec.example_value_type}! Error thrown was {e}") from e

#     def generate_fields(self, data, parent_name=False):
#         mapcreate = self.env['zbs.backend.model.field']
#         if not data or not isinstance(data,dict):
#             return
#         else:
#             for key, value in data.items():
#                 name = key
#                 if parent_name:
#                     name = parent_name + "." + key
#                 if self.env['zbs.backend.model.field'].search([('backend_model_id','=',self.id),('name','=',key)]):
#                     continue
#                 if isinstance(value,dict) or isinstance(value,list):
#                     t = mapcreate.create({
#                         "name": name,
#                         "backend_model_id": self.id
#                     })
#                     if isinstance(value,list):
#                         for val in value:
#                             self.generate_fields(val,t.id)
#                     else:
#                         self.generate_fields(value,t.id)
#                 else:
#                      t = mapcreate.create({
#                         "name": name,
#                         "backend_model_id": self.id
#                     })

# class BackendModelField(models.Model):
#     _name="zbs.backend.model.field"

#     name = fields.Char("Name")
#     backend_model_id = fields.Many2one("zbs.backend.model",string="Backend Model")
