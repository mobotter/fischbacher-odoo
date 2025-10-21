# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from .. import odoorpc
import logging
from .odoorpc_wrapper import RPCWrapper

logger = logging.getLogger("zbsync.grabber.odoo")


class Domain(models.Model):
    _inherit = ["zbs.domain", "zbs.xport.mixin"]
    _name = "zbs.domain.odoo"
    _description = "Zync Domain Odoo"

    parent_id = fields.Many2one("zbs.grabber.odoo")


class OdooGrabber(models.Model):
    _inherit = ["zbs.grabber", "zbs.odoo.mixin.connection", "zbs.domains.mixin"]
    _name = "zbs.grabber.odoo"
    _description = "Odoo Grabber"

    offset = fields.Integer("Offset", default=0, tracking=True)
    limit = fields.Integer("Limit", default=0, tracking=True)
    order = fields.Char("Order", default="id", tracking=True)
    domain_ids = fields.One2many("zbs.domain.odoo", tracking=True)
    fields_to_read = fields.Char("Fields (comma separated)", tracking=True)
    is_local_connection = fields.Boolean(related="connection_id.is_local_connection")
    context = fields.Text(
        "Odoo Context", help="e.g. {'no_reset_password': True}", default="{}"
    )
    lang_id = fields.Many2one("res.lang", string="Language")
    lang = fields.Char(related="lang_id.code")
    company_id = fields.Many2one("res.company", string="Company")
    odoo_as = fields.Selection(
        [
            ("json", "JSON"),
            ("browse", "Browsable Object"),
        ],
        string="Format-Type",
        default="json",
        tracking=True,
        required=True,
    )

    def _slugme(self, instances, _fields):
        for inst in instances:
            for k in _fields:
                inst[k] = self._slug(inst[k])
            del inst
        return instances

    def _get_fields(self):
        self.ensure_one()
        if self.fields_to_read:
            return self.fields_to_read.split(",")
        all_fields = list(self.connection_id._get_fields_of_obj(self.model).keys())
        return all_fields

    def process(self, instance, data, errors=None):
        result_instances = None
        self.connection_id.clear_caches()
        context = self.connection_id._get_context(
            self.context, dict(instance=instance, data=data)
        )
        context["lang"] = self.lang
        self = self.with_context(ODOORPC_CONTEXT=context)

        for index, record in self.env["zebrooset"].iterate(data):
            breakpoint()
            domain = self.resolve_domain(instance, data=record, record=record) or []

            obj = self.connection_id._get_obj(self.model)

            obj = self.connection_id._set_company_context(obj)
            instance_ids = self.connection_id._odoo_search(
                obj,
                domain,
                return_ids=True,
                order=self.order,
                limit=self.limit,
                offset=self.offset,
            )

            batch = self.env.context["zbs_batch"]

            if self.odoo_as == "json":
                _fields = self._get_fields()
                instances = obj.browse(instance_ids)
                instances = self._slugme(instances.read(_fields) or [], _fields)
                self._apply_keep_input(index, record, data, instances)
                if result_instances is None:
                    result_instances = []
                result_instances += instances

            elif self.connection_id.is_local_connection:
                if result_instances is None:
                    result_instances = self.env[self.model]
                instances = obj.browse(instance_ids)
                result_instances |= instances

            elif self.odoo_as == "browse":
                instances = None
                if result_instances is None:
                    result_instances = RPCWrapper(
                        self.connection_id.id, obj, instance_ids
                    )
                else:
                    result_instances.ids += instance_ids

            else:
                raise NotImplementedError(self.odoo_as)
            del instances
            del obj

        return instance.Result(result_instances)

    @api.model
    def _slug(self, v):
        if isinstance(v, odoorpc.models.BaseModel):
            return v.id
        if isinstance(v, int):
            return v
        if not v:
            return False
        if isinstance(v, (tuple, list)) and len(v) > 1:
            return v[0]
        return v
