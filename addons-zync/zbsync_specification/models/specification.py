# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, fields
import json
import yaml


class OpenApiSpecification(models.Model):
    _inherit = ["mail.thread"]
    _name = "zbs.api.specification"
    _description = "Zync API Specification"

    name = fields.Char("Name")
    specification_type = fields.Selection(
        [("json", "json"), ("yaml", "yaml")],
        string="Specification Type",
        default="json",
    )
    description = fields.Text("Description")
    summary = fields.Text("Summary")
    version = fields.Char("Version", compute="_compute_version")
    specification = fields.Char("Specification")
    pipeline_ids = fields.Many2many("zbs.pipeline", string="Pipelines")
    api_version = fields.Char("OpenAPI Version")
    major_version = fields.Integer("MAJOR", tracking=True)
    minor_version = fields.Integer("MINOR", tracking=True)
    patch_version = fields.Integer("PATCH", tracking=True)

    def create_specification(self):
        info = {
            "title": self.name,
            "version": self.version,
            "description": self.description,
        }
        servers = [
            {
                "url": (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param(key="web.base.url", default=False)
                )
                + "/zync",
                "description": "Main Server API",
            }
        ]
        spec = {
            "openapi": self.api_version,
            "info": info,
            "servers": servers,
            "paths": {},
        }
        compdict = {"schemas": {}}

        for pipeline in self.pipeline_ids:
            start = pipeline.line_ids.filtered(
                lambda x: x.worker_id._name == "zbs.start"
            )

            start_worker = self.env[start.worker_id._name].browse(start.worker_id.id)
            config = start_worker.rest_config_id

            rtype = self.generate_request(start_worker, config)
            path_params = config.parameter_ids.filtered(
                lambda x: x.parameter_type == "path"
            )
            if path_params:
                for path_param in path_params:
                    spec = self.generate_path(
                        spec,
                        start_worker.identifier,
                        start_worker.request_method,
                        path_param,
                        rtype,
                    )
            else:
                spec = self.generate_path(
                    spec,
                    start_worker.identifier,
                    start_worker.request_method,
                    False,
                    rtype,
                )
            if config.payload_scheme_id or config.response_id.content_scheme_id:
                compdict = self.generate_components(compdict, config)

        spec["components"] = compdict
        spec = self.generate_authorizer_schemes(spec)
        spec = self.generate_error_schemes(spec)
        if self.specification_type == "json":
            self.specification = json.dumps(spec)
        elif self.specification_type == "yaml":
            self.specification = yaml.dump(spec)

    def generate_authorizer(self, start_worker, spec):
        if start_worker.authorizer_id:
            spec["security"] = []
            auth = {}
            auth["bearerAuth"] = []
            spec["security"].append(auth)

        return spec

    def generate_authorizer_schemes(self, spec):
        components = {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        }
        spec["components"] = components
        return spec

    def generate_error_schemes(self, spec):
        spec["components"]["error"] = {}
        spec["components"]["error"]["properties"] = {}
        for t in ["name", "code", "message"]:
            spec["components"]["error"]["properties"][t] = {}
            spec["components"]["error"]["properties"][t][
                "description"
            ] = f"{t} of the error."
            spec["components"]["error"]["properties"][t]["type"] = "string"
        return spec

    def generate_path(self, spec, identifier, request_method, path_param, rtype):
        if path_param:
            identifier = identifier + "/{" + path_param.field + "}"
        path = f"/{identifier}"
        is_path_created = path in spec["paths"]
        if not is_path_created:
            spec["paths"].setdefault("/" + identifier, {})
        spec["paths"][path][str(request_method).lower()] = rtype
        return spec

    def generate_request(self, start_worker, config):
        tags = [start_worker.rest_config_id.request_group.name]
        request = {
            "tags": tags,
            "description": start_worker.description or "",
            "summary": start_worker.rest_config_id.summary or "",
        }
        params = config.compute_parameter()
        if params:
            request["parameters"] = params
        if config.response_load:
            request["responses"] = {}
            request["responses"] = config.compute_response_load()
        if config.payload:
            request["requestBody"] = config.compute_payload()
        request = self.generate_authorizer(start_worker, request)
        return request

    def generate_components(self, compdict, config):
        for k, v in config.compute_component().items():
            compdict["schemas"][k] = v
        return compdict

    def _compute_version(self):
        for rec in self:
            rec.version = f"{rec.major_version}.{rec.minor_version}.{rec.patch_version}"
