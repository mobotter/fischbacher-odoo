# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models


class CreateMappingWizard(models.TransientModel):
    _name = "zbs.create.mapping.wizard"
    _description = "Zync create mapping wizard"

    mapper_id = fields.Many2one("zbs.mapper", "Mapper")

    name = fields.Char("Name")
    mapping_direction = fields.Selection(
        [
            ("import", "Import to Local Odoo"),
            ("export", "Export to External Model"),
            ("transfer", "Transfer Two Non-Odoo Models"),
        ]
    )
    odoo_model_id = fields.Many2one("ir.model", "Odoo Model")
    backend_model_id = fields.Many2one("zbs.backend.model", "External Model")
    transfer_model_id = fields.Many2one("zbs.backend.model", "Transfer Model")
    from_field_ids = fields.One2many(
        "zbs.create.mapping.wizard.field",
        "wizard_id",
        "Fields to Map",
        domain="[('direction','=','from')]",
    )
    to_field_ids = fields.One2many(
        "zbs.create.mapping.wizard.field",
        "wizard_id",
        "Allowed Fields",
        domain="[('direction','=','to')]",
    )

    @api.onchange(
        "mapping_direction", "odoo_model_id", "backend_model_id", "transfer_model_id"
    )
    def fill_fields(self):
        self.from_field_ids = [(5, 0, 0)]
        self.to_field_ids = [(5, 0, 0)]
        parse_from_fields = False
        parse_to_fields = False
        if self.mapping_direction == "import":
            parse_from_fields = (
                self.backend_model_id.name,
                self.backend_model_id.get_data(),
            )
            parse_to_fields = (
                self.odoo_model_id.name,
                self.odoo_model_id.field_id.mapped("name"),
            )
        elif self.mapping_direction == "export":
            parse_from_fields = (
                self.odoo_model_id.name,
                self.odoo_model_id.field_id.mapped("name"),
            )
            parse_to_fields = (
                self.backend_model_id.name,
                self.backend_model_id.get_data(),
            )
        else:
            parse_from_fields = (
                self.backend_model_id.name,
                self.backend_model_id.get_data(),
            )
            parse_to_fields = (
                self.transfer_model_id.name,
                self.backend_model_id.get_data(),
            )

        if not parse_from_fields[0]:
            pass
        else:
            self.from_field_ids = [
                (
                    6,
                    0,
                    self.generate_fields(
                        "from", parse_from_fields[1], parse_from_fields[0]
                    ),
                )
            ]

        if not parse_to_fields[0]:
            pass
        else:
            self.to_field_ids = [
                (
                    6,
                    0,
                    self.generate_fields("to", parse_to_fields[1], parse_to_fields[0]),
                )
            ]

    def generate_fields(self, direction, data, model_name, parent_name=False):
        fields = []
        mapcreate = self.env["zbs.create.mapping.wizard.field"]
        if not data:
            return []
        if isinstance(data, list):
            for key in data:
                t = mapcreate.create(
                    {
                        "name": key,
                        "model_name": model_name,
                        # "wizard_id": self.id
                    }
                )
                fields.append(t.id)
        else:
            for key, value in data.items():
                name = key
                if parent_name:
                    name = parent_name + "." + key
                if mapcreate.search([("wizard_id", "=", self.id), ("name", "=", key)]):
                    continue
                if isinstance(value, dict) or isinstance(value, list):
                    t = mapcreate.create(
                        {
                            "name": name,
                            "direction": direction,
                            "model_name": model_name,
                            "wizard_id": self.id,
                        }
                    )
                    if isinstance(value, list):
                        for val in value:
                            self.generate_fields(direction, val, model_name, name)
                        else:
                            self.generate_fields(direction, value, model_name, name)
                else:
                    t = mapcreate.create(
                        {
                            "name": name,
                            "direction": direction,
                            "model_name": model_name,
                            "wizard_id": self.id,
                        }
                    )
                fields.append(t.id)
        return fields

    def wizard_confirm(self):
        mapping = self.env["zbs.mapping"]
        for t in self.from_field_ids:
            if t.action in ["list", "object", "code"] or t.mapped_field_id:
                mapping.create(
                    {
                        "step_id": self.mapper_id.id,
                        "name": t.name,
                        "field_source": t.name,
                        "field_dest": t.mapped_field_id.name,
                        "action": t.action,
                    }
                )
        return True


class CreateMappingWizardField(models.TransientModel):
    _name = "zbs.create.mapping.wizard.field"
    _description = "Zync create mapping wizard field"

    name = fields.Char("Source Field")
    direction = fields.Selection([("from", "from"), ("to", "to")])
    model_name = fields.Char("Source Model")
    wizard_id = fields.Many2one("zbs.create.mapping.wizard", "Wizard")
    allowed_field_ids = fields.One2many(
        comodel_name="zbs.create.mapping.wizard.field",
        compute="_compute_allowed_fields",
        string="Allowed Fields",
    )
    mapped_field_id = fields.Many2one(
        "zbs.create.mapping.wizard.field",
        "Destination Field",
        domain="[('id','in',allowed_field_ids)]",
    )

    may_miss = fields.Boolean("Source may miss")
    skip_if_empty = fields.Boolean("Skip if empty")
    unlink_subrecords = fields.Boolean("Unlink Subrecords")
    filter_to_delta = fields.Boolean(
        "Filter Delta",
        default=False,
    )
    no_create = fields.Boolean("No Create")
    no_update = fields.Boolean("No Update")
    default_value = fields.Boolean(
        "Default Value",
        help="Only set at write if False on other side",
    )
    pyfunc_id = fields.Many2one(
        "zbs.mapping.pyfunc",
        string="Function",
    )
    skip_record_expr = fields.Text(
        "Expression to skip whole record",
    )

    action = fields.Selection(
        [
            ("direct", "=>"),
            ("object", "{}"),
            ("list", "[]"),
            ("eval", "code"),
            ("mapped_values", "Value Mappings"),
            ("lookup", "Lookup"),  # TODO implement that record is created if not found
            # TODO trurnit lookup auf many2many auch machen z.B. wenn komma getrennt
            # environment values: they can be grabbed from data; is collected by file grabbers then
        ],
        string="Action",
        required=True,
        default="direct",
    )
    format_value = fields.Text(
        "Format Expression",
        help="str(value).strip()",
    )
    code = fields.Char("Code")
    is_key = fields.Boolean("Is Key")
    comment = fields.Text(
        "Comment",
    )
    mapped_value_ids = fields.One2many(
        "zbs.mapping.mapvalues",
        "mapper_id",
        string="Mapped Values",
    )
    strict_mapped_types = fields.Boolean(
        "Strict Mapped Types",
    )
    lookup_model = fields.Char(
        "Lookup Model",
    )
    lookup_field = fields.Char(
        "Lookup Field",
    )
    lookup_operator = fields.Selection(
        [("=", "="), ("ilike", "ilike"), ("like", "like")],
        string="Lookup Operator",
        default="ilike",
    )
    skip_if = fields.Selection(
        [
            ("never", "Never"),
            (
                "not_in_envs",
                "If not in env.fields",
            ),  # trigger method hook puts changed fields into 'fields'
        ],
    )
    output_stream = fields.Selection(
        [("env", "Environment")],
    )

    @api.depends("wizard_id.to_field_ids")
    def _compute_allowed_fields(self):
        for rec in self:
            if rec.wizard_id.to_field_ids:
                rec.allowed_field_ids = rec.wizard_id.to_field_ids.ids
            else:
                rec.allowed_field_ids = False


class CreateMappingWizardFieldAllowed(models.TransientModel):
    _inherit = "zbs.create.mapping.wizard.field"
    _name = "zbs.create.mapping.wizard.field.allowed"

    _description = "Wizard to create allowed fields"
