# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models
from contextlib import contextmanager
from functools import partial


class WebUrl(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.web.url"
    _description = "Web URL"

    name = fields.Char("URL", compute="_compute_name", store=True)
    identifier = fields.Char("Identifier")
    url_ids = fields.One2many("zbs.web.url.per_env", "url_id", "URLs")

    def _get_effective_url(self):
        instance = self.env.context["zbs_instance"]
        env = instance.environment_id
        return self.env["zbs.tools"].expect_one(
            self.url_ids.filtered(
                lambda x: env in x.environment_ids if env else not x.environment_ids
            )
        )

    @api.depends("identifier", "url_ids", "url_ids.name")
    def _compute_name(self):
        for record in self:
            name = ", ".join(set(filter(bool, record.url_ids.mapped("name"))))
            if self.identifier:
                record.name = f"{self.identifier} - {name}"
            else:
                record.name = name

    @contextmanager
    def connect(self, method, method_str, params):
        url = self._get_effective_url()
        params["proxies"] = url.proxy_ids._get_for_requests()
        auth = url.auth_id
        if auth:
            with auth._do_auth(method, method_str, params) as method:
                yield partial(method, **params)
        else:
            yield partial(method, **params)

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get("name") and not val.get("url_ids"):
                env = self.env["zbs.environment"].sudo().search([])
                val["url_ids"] = [
                    (0, 0, {"name": val["name"], "environment_ids": env.ids})
                ]
        res = super().create(vals_list)
        res._compute_name()
        return res


class WebUrlPerEnv(models.Model):
    _inherit = ["zbs.xport.mixin"]
    _name = "zbs.web.url.per_env"
    _description = "Set URLs and attach them to different environments"

    name = fields.Char("Name (URL)", required=True)
    url_id = fields.Many2one(
        "zbs.web.url", "URL", required=True, ondelete="cascade", xport_ignore=True
    )
    auth_id = fields.Many2one("zbs.connection.web.auth", string="Auth")
    proxy_ids = fields.Many2many("zbs.web.proxy", string="Proxies")
    environment_ids = fields.Many2many(
        "zbs.environment",
        string="Environment",
    )
