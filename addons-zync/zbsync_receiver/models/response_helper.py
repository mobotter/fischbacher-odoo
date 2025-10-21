# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, api
import json


class ResponseBuilder(models.AbstractModel):
    _name = "zbs.receiver.response.helper"
    _description = "Response Helper"

    @api.model
    def _build_http_response(self, response):
        from odoo.http import Response

        if not isinstance(response, dict):
            return response
        response = Response(
            json.dumps(response["body"]),
            headers=response["headers"],
            status=response["http_status_code"],
        )
        return response

    @api.model
    def _build_http_error_response(self, exception, httpcode, odoocode):
        code = odoocode or "OD500"
        if hasattr(exception, "code"):
            code = exception.code
        return self._build_http_response(
            {
                "body": {
                    "code": code,
                    "error": str(exception),
                },
                "headers": {
                    "Content-Type": "application/json",
                },
                "http_status_code": httpcode,
            }
        )
