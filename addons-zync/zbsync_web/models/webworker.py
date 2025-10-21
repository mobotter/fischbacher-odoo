# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import time
import requests
from contextlib import contextmanager
from xml.etree import ElementTree
from odoo import api, fields, models
from odoo.addons.zbsync.models.zebrooset import ZebrooSet, _WrappedList

import logging

logger = logging.getLogger("zbsync.webworker")


class BreakPagination(Exception):
    pass


class WebWorker(models.Model):
    _inherit = ["zbs.grabber"]

    _name = "zbs.web.worker"
    _description = "Web Grabber / Dumper"

    url_id = fields.Many2one("zbs.web.url", string="Root URL")
    timeout = fields.Integer("Timeout (seconds)", default=10)
    retry_pattern = fields.Char(
        "Retry Pattern",
        help="""Only applied to Queue Jobs.
            Defines a retry pattern, in seconds, to be followed on any error.\n
            E.g. 1,5,10,20""",
    )
    path = fields.Text("Path")
    request_arg_ids = fields.One2many(
        "zbs.web.request_args", "worker_id", string="Request Parameters"
    )
    body = fields.Text(
        "Body",
        help="Request body. Should match the Request Content Type.",
    )
    code_next_page = fields.Text(
        "Next URL Page",
        help="""Expected content: zSync Code
                Executed before fetching the next page, to get next request URL.\n
                Eg. project.com/records/start_index={response.last_index + 1}&pagination_size={response.page_size}""",
    )
    extract_path = fields.Text(
        "Data Field",
        help="""Expected content: zSync Code
                Retrieves data from specified field in the response body.""",
    )
    request_content_type = fields.Selection(
        [
            ("application/json", "application/json"),
            ("graphql", "GraphQL Query"),
            ("form_url_encoded", "form_url_encoded"),
            ("application/x-www-form-urlencoded", "application/x-www-form-urlencoded"),
            ("html", "broken! - html"),
            ("xml", "broken! - xml"),
            ("text", "broken! - text"),
            ("text/html", "text/html"),
            ("application/xml", "application/xml"),
            ("text/plain", "text/plain"),
        ],
        string="Request Content Type",
    )
    response_content_type = fields.Selection(
        [
            ("json", "application/json"),
            ("html", "text/html"),
            ("xml", "application/xml"),
            ("text", "text/plain"),
            ("raw", "Raw-Content"),
        ],
        string="Response Content Type",
    )
    method = fields.Selection(
        [
            ("get", "GET"),
            ("post", "POST"),
            ("put", "PUT"),
            ("patch", "PATCH"),
            ("delete", "DELETE"),
            ("head", "HEAD"),
            ("options", "OPTIONS"),
        ],
        string="Method",
        required=False,
    )
    return_response_headers = fields.Boolean("Retrieve Reponse Headers")
    dont_send_body = fields.Boolean("Send without body")

    def process(self, instance, data, errors=None):
        res = super().process(instance, data, errors=errors)
        return res

    def _extract_data(self, response):
        if not self.extract_path:
            return response
        try:
            response = self.env["zbs.tools"].zebrooset(response)
        except:
            pass
        response = self.env["zbs.tools"]._exec_get_result(
            self.extract_path, {"response": response}
        )
        return response

    def process_record(self, instance, index, record, data, errors=None):
        pages = []
        next_page_url = None
        headers = []
        cookies = False

        iteration = 1
        while True:
            result_record, response = self._process(
                index, record, data, force_url=next_page_url
            )
            headers.append(dict(response.headers))
            if not self.code_next_page:
                pages = self._extract_data(result_record)
                headers = headers[0]
                cookies = response.cookies
                break

            url = self.url_id._get_effective_url().name
            if self.response_content_type in ["json"]:
                response = self.env["zebrooset"].rs(result_record)
            else:
                response = result_record
            next_page_url = self.env["zbs.tools"]._exec_get_result(
                self.code_next_page,
                {
                    "response": response,
                    "pagenr": iteration,
                    "url": url,
                    "BreakPagination": BreakPagination,
                },
            )
            response = self._extract_data(response)
            if isinstance(response, ZebrooSet):
                if isinstance(response._d, list):
                    pages += result_record._d
                else:
                    pages.append(result_record)
            elif isinstance(response, _WrappedList):
                pages += response._l
            else:
                pages.append(result_record)
            if not next_page_url:
                break
            iteration += 1

        if self.return_response_headers:
            return {"headers": headers, "response": pages, "cookies": cookies}
        else:
            return pages

    def _process(self, index, record, data, force_url=None):

        with self._request(index, record, data, force_url=force_url) as response:
            params = {
                "instance": self.env.context.get("zbs_instance"),
                "record": record,
                "index": index,
                "data": data,
                "response": response,
            }
            if self.response_content_type == "json":
                return self._process_json(**params), response

            elif self.response_content_type == "raw":
                return self._process_raw(**params), response

            elif self.response_content_type == "xml":
                return self._process_xml(**params), response
            elif self.response_content_type == "html":
                params["subtype"] = "html"
                return self._process_html(**params), response
            elif self.response_content_type == "text":
                params["subtype"] = "plain"
                return self._process_html(**params), response
            else:
                raise NotImplementedError(self.response_content_type)

    def _get_request_method(self):
        if not self.method:
            raise ValueError("Please define a web method!")
        meth = getattr(requests, self.method)
        return meth

    def _eval_response_state(self, response):
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise

    def _eval_path(self, index, record, data):
        return self._eval_expression(
            self.path,
            index,
            record,
            data,
            input=self.env.context.get("zbs_prepared_input_data"),
            expects_string_if_oneline=True,
        )

    def _build_url(self, index, record, data):
        res = self.url_id._get_effective_url().name
        if res.endswith("/"):
            res = res[:-1]
        path = self._eval_path(index, record, data)
        if not path.startswith("/"):
            path = "/" + path
        return res + path

    def _get_params(self, index, record, data):
        url = self._build_url(index, record, data)
        data = {
            "url": url,
            "timeout": self.timeout,
        }
        data.update(self._get_request_args(index, record, data))
        if not self.dont_send_body:
            body = self._prepare_body_content(index, record, data)
            if body is not None:
                data.update(body)

        return data

    def _prepare_body_content(self, index, record, data):
        data = {}
        value = record
        if self.body:
            value = self._eval_expression(
                self.body,
                index,
                record,
                data,
                input=self.env.context.get("zbs_prepared_input_data"),
            )

        if value is None:
            return {}

        if self.request_content_type in ["application/json"]:
            data["json"] = self.env["zbs.tools"]._as_python_object(value)

        elif self.request_content_type in [
            "text/html",
            "application/xml",
            "text/plain",
        ]:
            content = self._extract_content(value)
            data["data"] = str(content)
        else:
            content = self._extract_content(value)
            data["data"] = content
        return data

    def _get_request_args(self, index, record, data):
        self.ensure_one()
        headers, cookies = {}, {}
        headers["Content-Type"] = self.request_content_type
        instance = self.env.context.get("zbs_instance")
        _globals = instance._get_default_objects(
            {
                "index": index,
                "record": record,
                "input": data,
            }
        )

        for request_arg in self.request_arg_ids:
            value = self.env["zbs.tools"]._eval_oneliner_or_code(
                request_arg.value, _globals
            )
            if request_arg.type == "header":
                headers[request_arg.name] = value
            elif request_arg.type == "cookie":
                cookies[request_arg.name] = value
            else:
                raise NotImplementedError(request_arg.type)
        res = {}
        res["headers"] = headers
        if cookies:
            res["cookies"] = cookies
        return res

    @contextmanager
    def _request(self, index, record, data, force_url=None):
        method = self._get_request_method()
        params = self._get_params(index, record, data)
        if force_url:
            params["url"] = force_url
        with self.url_id.connect(method, self.method, params) as callable:
            retry_pattern = self.parse_retry_pattnern()
            EX = None
            for sleep_time in retry_pattern:
                try:
                    response = callable()
                    self._eval_response_state(response)
                except requests.exceptions.ConnectionError as ex:
                    EX = ex
                    if sleep_time:
                        time.sleep(sleep_time)
                    else:
                        raise
                else:
                    break
            else:
                raise EX
            yield response

    def parse_retry_pattnern(self):
        retry_pattern = self.retry_pattern or ""
        if not retry_pattern:
            return [0]
        retry_pattern = list(map(lambda x: int(x.strip()), retry_pattern.split(",")))
        return retry_pattern

    def _process_json(self, index, instance, data, record, response):
        return response.json()

    def _process_raw(self, index, instance, data, record, response):
        return response.content

    def _process_xml(self, index, instance, data, record, response):
        tree = ElementTree.fromstring(response.content)
        return tree

    def _process_html(self, index, instance, data, record, response, subtype):
        res = response.text
        return res

    @api.constrains("path", "extract_path", "code_next_page")
    def _strip(self):
        for rec in self:
            for field in ["path", "extract_path", "code_next_page"]:
                value = rec[field] or ""
                if value.strip() != value:
                    rec[field] = value.strip()
