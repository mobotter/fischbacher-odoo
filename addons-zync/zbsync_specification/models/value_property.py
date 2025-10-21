# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, models, fields


class ValueProperty(models.Model):
    _name = "zbs.value.property"
    _description = "Zync API Value Property"

    name = fields.Char("Name", required=True)
    technical_name = fields.Char(
        "Technical Name", compute="_compute_tech_name", store=True
    )
    property_id = fields.Many2one("zbs.value.property", "Property Id")
    object_appearance = fields.Selection(
        [("inline", "inline"), ("property", "property")]
    )
    # I actively decided to not allow "OneOf"
    property_type_id = fields.Many2one(
        "zbs.value.property.type", string="Property Values"
    )
    property_type_name = fields.Char(
        related="property_type_id.name", string="Property Type"
    )
    field_ids = fields.One2many("zbs.value.property", "property_id", string="Fields")
    required = fields.Boolean("Required")
    allowed_values = fields.Char(
        "Enum Allowed Values", help="Comma-Separated allowed values"
    )
    effective_allowed_values = fields.Char(compute="_compute_allowed_values")
    example = fields.Char("Example Value")
    description = fields.Char("description")

    @api.depends("name")
    def _compute_tech_name(self):
        for rec in self:
            rec.technical_name = rec.name.lower().replace(" ", "_")

    def property_dict(self):
        prop = {}
        if not self.field_ids and self.property_id:
            prop[self.name] = {
                "id": self.id,
                "name": self.property_type_name,
                "required": self.required,
                "property_id": self.property_id.id,
            }
        elif self.property_id:
            if self.property_type_name == "array":
                prop[self.name] = []
                for f in self.field_ids:
                    prop[self.name].append(f.property_dict())
            else:
                prop[self.name] = {}
                for f in self.field_ids:
                    prop[self.name] = f.property_dict()
        else:
            for f in self.field_ids:
                if f.required:
                    prop[f.name] = f.property_type_id.name
        return prop

    @property
    def minimum_property_dict(self):
        return self.property_dict() if self.required else False

    def check_value_type(self, value):
        if self.property_type_name == "string":
            if not isinstance(value, str):
                return False
        if self.property_type_name == "boolean":
            if not isinstance(value, bool):
                return False
        if self.property_type_name == "integer":
            if not isinstance(value, int):
                return False
        if self.property_type_name == "float":
            if not isinstance(value, float):
                return False
        if self.property_type_name == "array":
            if not isinstance(value, list):
                return False
        if self.property_type_name == "object":
            if not isinstance(value, dict):
                return False
        return True


class DataTypeKeyword(models.Model):
    _name = "zbs.value.property.keyword"
    _description = "Zync Value Property Keyword"

    name = fields.Char("Name")
    format = fields.Char("Format or Pattern")
    available_for_type_id = fields.Many2many(
        "zbs.value.property.type", string="Available For"
    )


class PropertyType(models.Model):
    _name = "zbs.value.property.type"
    _description = "Zync Value Property Type"

    name = fields.Char("Name")
    format = fields.Char("Format")
    description = fields.Char("Description")
    allowed_keyword_ids = fields.Many2many(
        "zbs.value.property.keyword", string="Allowed Keywords"
    )
