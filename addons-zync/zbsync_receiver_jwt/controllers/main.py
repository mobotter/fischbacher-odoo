# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import json
from odoo import http
from odoo.http import request

try:
    from odoo.http import AuthenticationError
except:

    class AuthenticationError(Exception):
        pass


class Authentication(http.Controller):
    @http.route(
        "/zync/clientTokens",
        auth="public",
        type="http",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def handler(self, **params):
        try:
            web_auth = (
                request.env["zbs.receive.authorizer"]
                .sudo()
                .search([("auth_type", "=", "jwt")], limit=1)
            )

            body = json.loads(request.httprequest.data)
            response_builder = request.env["zbs.receiver.response.helper"]
            if "username" not in body:
                e = "Bad Request. Required field username is missing."
                return response_builder._build_http_error_response(e, 400, "OD400")
            if "password" not in body:
                e = "Bad Request. Required field password is missing."
                return response_builder._build_http_error_response(e, 400, "OD400")
            username = body["username"]
            password = body["password"]
            password = web_auth._unsalt_password(password)
            payload = body.get("payload", {})

            username, password = request.env[
                "zbs.receive.authorizer"
            ]._hook_username_password(username, password, payload)
            uid = request.env["res.users"].authenticate(
                request.env.cr.dbname, username, password, {}
            )
            if not uid:
                raise Exception(
                    "UID Not found, Unauthorized. Error while trying to access."
                )

            token, expdate = web_auth._make_token(uid, payload)

            response = response_builder._build_http_response(
                {
                    "body": {
                        "token": token.decode("utf-8"),
                        "expiration_date": str(expdate),
                    },
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "http_status_code": 202,
                }
            )
            return response

        except Exception as e:
            return response_builder._build_http_error_response(e, 401, "OD4001")
