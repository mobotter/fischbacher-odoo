# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import collections
import json
from odoo import api, fields, models
from odoo.osv import expression


class ZbsRestConfig(models.Model):
    _name = "zbs.rest.config"
    _description = "Zync API REST Config"

    name = fields.Char(compute="_compute_name", string="Name")
    short_name = fields.Char("Shortname")
    request_method = fields.Selection(
        [("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("DELETE", "DELETE")],
        string="Request Type",
    )
    request_type = fields.Selection(
        [
            ("application/json", "application/json"),
            ("application/text", "application/text"),
        ],
        string="Payload Type",
        default="application/json",
    )
    parameters = fields.Char(string="Parameters", compute="_compute_parameters")
    request_group = fields.Many2one("zbs.start.request.group", string="Request Group")
    description = fields.Char("Description")
    summary = fields.Char("Summary")
    example_ids = fields.One2many(
        comodel_name="zbs.rest.config.example",
        inverse_name="zbs_rest_config_id",
        string="Examples",
        copy=True,
    )
    payload = fields.Char(string="Payload", compute="_compute_payload")
    component = fields.Char(string="Component", compute="_compute_component")
    payload_scheme_id = fields.Many2one("zbs.value.property", "Payload Scheme")
    parameter_ids = fields.One2many(
        "zbs.payload.parameter", "config_id", "Parameter", copy=True
    )
    response_load = fields.Char(
        string="Response Load", compute="_compute_response_load"
    )
    response_id = fields.Many2one("zbs.stop.response", string="Responses")
    error_ids = fields.One2many(
        "zbs.response.error", "config_id", string="Possible Errors", copy=True
    )

    @api.depends("request_group", "request_method")
    def _compute_name(self):
        for rec in self:
            rec.name = "{}-{}-{}".format(
                rec.request_group.name, rec.request_method, rec.short_name
            )

    # not yet implemented
    def _check_parameters(self):
        return True

    # not yet implemented
    def _check_payload_data(self, data):
        if self.request_method in ["PUT", "POST"]:
            scheme = self.payload_scheme_id
            self._check_data(scheme, data)
        return True

    def _check_response_data(self, data):
        scheme = self.response_id.content_scheme_id
        self._check_data(scheme, data)
        return True

    def _check_data(self, scheme, data):
        min_dict = scheme.minimum_property_dict
        if not min_dict or not data:
            return
        for key in self.get_keys(min_dict):
            for index, d in data._iterate_records():
                if not d:
                    return
                data_keys = self.get_keys(d)
                if not key in data_keys:
                    raise Exception("Required Key Value {} Missing!".format(key))
                break

    def get_keys(self, d):
        klist = []
        for k, v in d.items():
            klist.append(k)
            if isinstance(v, dict):
                klist.append(self.get_keys(v))
        return klist

    @api.depends("payload_scheme_id")
    def _compute_payload(self):
        load = self.compute_payload()
        if load:
            self.payload = json.dumps(dict(load), indent=4)
        else:
            self.payload = ""

    @api.depends("payload_scheme_id")
    def _compute_component(self):
        self.component = json.dumps(self.compute_component(), indent=4)

    @api.depends("parameter_ids")
    def _compute_parameters(self):
        self.parameters = json.dumps(self.compute_parameter(), indent=4)

    def compute_payload(self):
        if not self.payload_scheme_id:
            return False
        body = collections.defaultdict(dict)
        body["required"] = self.payload_scheme_id.required
        body["description"] = self.payload_scheme_id.description
        schema = {}
        schema["schema"] = {}
        schema["schema"]["$ref"] = "#/components/schemas/" + str(
            self.payload_scheme_id.technical_name
        )
        body["content"] = {}
        body["content"][self.request_type] = schema
        props = []
        for p in self.payload_scheme_id.field_ids:
            prop = collections.defaultdict(dict)
            prop[p.name]["type"] = p.property_type_id.name or ""
            if p.example:
                prop[p.name]["example"] = p.example
            if p.description:
                prop[p.name]["description"] = p.description
            props.append(dict(prop))
        if self.payload_scheme_id.object_appearance == "property":
            pass
        else:
            body["content"][self.request_type]["properties"] = props

        examples = self.example_ids.filtered(lambda x: x.example_type == "payload")
        if len(examples) > 1:
            body["content"][self.request_type]["schema"]["examples"] = {}
            for example in examples:
                body["content"][self.request_type]["schema"]["examples"][
                    example.name
                ] = example.get_api_dict()
        if len(examples) == 1:
            body["content"][self.request_type]["schema"]["example"] = {}
            body["content"][self.request_type]["schema"]["example"][
                examples[0].name
            ] = examples[0].get_api_dict()

        return dict(body)

    def compute_component(self):
        if not self.payload_scheme_id and not self.response_id.content_scheme_id:
            return {}
        scheme = {}
        scheme = self._create_component(self.payload_scheme_id, scheme)
        scheme = self._create_component(self.response_id.content_scheme_id, scheme)
        return scheme

    def _create_component(self, scheme, scheme_dict):
        prop = {}
        name = scheme.technical_name
        if not name:
            return scheme_dict
        # if scheme.field_ids and scheme.property_type_id.name == 'object':
        scheme_dict[name] = {}
        scheme_dict[name]["type"] = scheme.property_type_id.name
        for field in scheme.field_ids:
            if field.property_type_id.name == "object":
                scheme_dict = self._create_component(field, scheme_dict)
            prop = self._create_property(prop, field)
        scheme_dict[name]["properties"] = prop

        rq = self.compute_required_items(scheme)
        if rq:
            scheme_dict[name]["required"] = rq
        return scheme_dict

    def _create_property(self, prop, field):
        prop[field.name] = {}
        if field.field_ids and field.property_type_id.name == "object":
            if field.object_appearance == "property":
                prop[field.name][
                    "$ref"
                ] = f"#/components/schemas/{field.technical_name}"
            return prop
        prop[field.name]["type"] = field.property_type_id.name
        if field.field_ids and field.property_type_id.name == "array":
            prop[field.name]["items"] = {}
            prop[field.name]["items"]["properties"] = {}
            for f in field.field_ids:
                prop[field.name]["items"]["properties"] = self._create_property(
                    prop[field.name]["items"]["properties"], f
                )
            return prop
        if field.field_ids and field.property_type_id.name == "object":
            for f in field.field_ids:
                prop[field.name] = self._create_property(prop[field.name], f)

        if field.allowed_values:
            enums = []
            for f in field.allowed_values.split(","):
                enums.append(f.strip())
            prop[field.name]["enum"] = enums
        if field.example:
            prop[field.name]["example"] = field.example
        if field.description:
            prop[field.name]["description"] = field.description
        return prop

    def compute_parameter(self):
        param = []
        if self.parameter_ids:
            for p in self.parameter_ids:
                parameter = p.generate_api_spec()
                param.append(parameter)
        return param

    def compute_required_items(self, scheme):
        req = []
        for field in scheme.field_ids:
            if field.required:
                req.append(field.name)
        return req

    def create_parameter_domain(self, type, value):
        domain = []
        if type == "path":
            param = self.parameter_ids.filtered(lambda x: x.parameter_type == type)
            if param:
                domain = [(param[0].field, "=", value)]
        if type == "query":
            for k, v in value.items():
                if k not in self.parameter_ids.mapped("field"):
                    raise Exception("Invalid Field in Request Domain")
                domain = expression.AND([domain, [(k, "=", v)]])
        return domain

    @api.depends(
        "response_id",
        "response_id.content_type",
        "response_id.content_scheme_id",
    )
    def _compute_response_load(self):
        self.response_load = json.dumps(self.compute_response_load(), indent=4)

    def compute_response_load(self):
        responses = {}
        r = self.response_id
        code = "200"
        responses[code] = {}

        ptype = {}
        schema = {}
        ptype["type"] = r.content_scheme_id.property_type_name
        schema["schema"] = ptype
        responses[code]["description"] = r.description
        responses[code]["content"] = {}
        responses[code]["content"][r.content_type] = schema
        if r.content_scheme_id.object_appearance == "property":
            responses[code]["content"][r.content_type]["schema"] = {}
            responses[code]["content"][r.content_type]["schema"]["$ref"] = (
                "#/components/schemas/" + str(r.content_scheme_id.technical_name)
            )
        else:
            responses[code]["content"][r.content_type]["schema"][
                "description"
            ] = r.description

        examples = self.example_ids.filtered(lambda x: x.example_type == "response")
        if len(examples) > 1:
            responses[code]["content"][r.content_type]["schema"]["examples"] = {}
            for example in examples:
                responses[code]["content"][r.content_type]["schema"]["examples"][
                    example.name
                ] = example.get_api_dict()
        if len(examples) == 1:
            responses[code]["content"][r.content_type]["schema"]["example"] = {}
            responses[code]["content"][r.content_type]["schema"]["example"][
                examples[0].name
            ] = examples[0].get_api_dict()

        for error in self.error_ids:
            responses[error.code.name] = {}
            responses[error.code.name]["description"] = error.description
            responses[error.code.name]["content"] = {}
            responses[error.code.name]["content"]["application/json"] = {}
            responses[error.code.name]["content"]["application/json"][
                "$ref"
            ] = "#/components/schemas/error"
            responses[error.code.name]["content"]["application/json"]["examples"] = {}
            for example in error.zbs_exception:
                responses[error.code.name]["content"]["application/json"]["examples"][
                    example.code
                ] = {}
                responses[error.code.name]["content"]["application/json"]["examples"][
                    example.code
                ]["value"] = {}
                responses[error.code.name]["content"]["application/json"]["examples"][
                    example.code
                ]["value"]["code"] = example.code
                responses[error.code.name]["content"]["application/json"]["examples"][
                    example.code
                ]["value"]["name"] = example.name
                responses[error.code.name]["content"]["application/json"]["examples"][
                    example.code
                ]["value"]["message"] = example.description
        return responses


class ZbsResponse(models.Model):
    _name = "zbs.stop.response"
    _description = "Zync Stop Response"

    name = fields.Char(string="Name", related="content_scheme_id.name")
    description = fields.Char("Description", related="content_scheme_id.description")
    config_id = fields.Many2one("zbs.rest.config", "Config")
    content_type = fields.Selection(
        [
            ("application/json", "application/json"),
            ("application/text", "application/text"),
        ],
        string="Content Type",
        default="application/json",
    )
    content_scheme_id = fields.Many2one("zbs.value.property", "Content Scheme")

    def compute_component(self):
        scheme = {}
        if not self.content_scheme_id:
            return scheme
        prop = collections.defaultdict(dict)
        name = self.content_scheme_id.technical_name
        scheme[name] = {}
        scheme[name]["type"] = self.content_scheme_id.property_type_id.name
        for field in self.content_scheme_id.field_ids:
            prop[field.name] = {}
            prop[field.name]["type"] = field.property_type_name or ""
            if field.allowed_values:
                enums = []
                for f in field.allowed_values.split(","):
                    enums.append(f.strip())
                prop[field.name]["enum"] = enums
            if field.example:
                prop[field.name]["example"] = field.example
            if field.description:
                prop[field.name]["description"] = field.description
        rq = self.compute_required_items()
        if rq:
            scheme[name]["required"] = rq
        scheme[name]["properties"] = dict(prop)
        return scheme

    def compute_required_items(self):
        req = []
        for scheme in self.content_scheme_id:
            for field in scheme.field_ids:
                if field.required:
                    req.append(field.name)
        return req


class ZbsStopProperty(models.Model):
    _name = "zbs.stop.property"
    _description = "Zync Stop Property"
    _inherit = "zbs.value.property"

    response_id = fields.Many2one("zbs.stop.response", string="Response")


class ZbsResponseError(models.Model):
    _name = "zbs.response.error"
    _description = "Zync Response Error"

    code = fields.Many2one("zbs.response.code", string="Code")
    description = fields.Char("Description")
    zbs_exception = fields.Many2many(
        "zbs.pipeline.exception", "response_id", "exception_id", string="Errors"
    )
    config_id = fields.Many2one("zbs.rest.config", string="Config ID")

    @api.constrains("code")
    def set_description(self):
        self.description = (
            self.code.description
            if self.code and not self.description
            else "Describe the occuring Error"
        )


class ZbsResponseCode(models.Model):
    _name = "zbs.response.code"
    _description = "Zync Response Code"

    name = fields.Char("Name")
    description = fields.Char("Description")

    def compute_spec(self):
        spec = {}
        if self.name == "200":
            return False
        description = {}
        description["description"] = self.description
        spec[self.code] = description
        return spec


class StartProperties(models.Model):
    _inherit = "zbs.value.property"
    _name = "zbs.start.property"
    _description = "Zync Start Property"

    start_id = fields.Many2one(comodel_name="zbs.start", string="Start")


class StartRequestGroup(models.Model):
    _name = "zbs.start.request.group"
    _description = "Zync Start Request Group"

    name = fields.Char("Name")


class ZbsREstConfigExample(models.Model):
    _name = "zbs.rest.config.example"
    _description = "Zync Rest Config Example"

    name = fields.Char("Name")
    example_json = fields.Text("Example JSON")
    example_type = fields.Selection(
        string="Example Type",
        selection=[
            ("payload", "Payload"),
            ("response", "Response"),
        ],
    )
    zbs_rest_config_id = fields.Many2one(
        comodel_name="zbs.rest.config", string="Config ID"
    )

    def get_api_dict(self):
        return json.loads(self.example_json)
