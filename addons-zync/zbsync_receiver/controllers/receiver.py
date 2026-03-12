# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.http import request, Controller
from ..exceptions import TokenExpirationException, TokenInvalidException
from odoo import http
from odoo.modules.registry import Registry as registry
from odoo.api import Environment
import json
import threading

from .. import URL
from odoo.addons.zbsync.exceptions import ZBSPipelineException


class PipelineNotFoundException(Exception):
    pass


class Receiver(Controller):
    @http.route(
        URL + "<identifier>" + "/" + "<parameter>",
        auth="public",
        type="http",
        methods=["GET", "POST", "PUT", "DELETE"],
        website=True,
        csrf=False,
    )
    def param_handler(self, identifier, parameter, **post):
        return self._handler(identifier, parameter=parameter, **post)

    @http.route(
        URL + "<identifier>",
        auth="public",
        type="http",
        methods=["GET", "POST", "PUT", "DELETE"],
        website=True,
        csrf=False,
    )
    def plain_handler(self, identifier, **post):
        return self._handler(identifier, **post)

    def _handler(self, identifier, parameter=None, **post):
        try:
            close = False
            if request.httprequest.headers.get("dbname"):
                dbname = request.httprequest.headers.get("dbname")
                if dbname != request.env.cr.dbname:
                    cr = registry(database_name=dbname).cursor()
                    close = cr
                    effective_env = Environment(
                        cr, request.env.user.id, request.env.context
                    )
                    request.env = effective_env
                else:
                    effective_env = request.env

            instance = False
            response_builder = request.env["zbs.receiver.response.helper"]
            try:
                instance = self.create_instance(
                    identifier, request.httprequest.method, **post
                )
                instance._raise_for_status()

            except TokenExpirationException as e:
                return response_builder._build_http_error_response(e, 401, "OD4001")
            except TokenInvalidException as e:
                return response_builder._build_http_error_response(e, 401, "OD4002")
            except PipelineNotFoundException as e:
                return response_builder._build_http_error_response(e, 404, "OD404")
            except Exception as e:
                return response_builder._build_http_error_response(e, 400, "OD4000")
            if not instance:
                return response_builder._build_http_response(
                    http.request.not_found("Path not found")
                )
            instance_env = instance._get_env()
            if parameter:
                instance_env["path_parameter"] = parameter
                instance_env["http_headers"] = request.httprequest.headers
                instance._set_env(instance_env)
            request.env.cr.commit()
            response = self.run_instance(instance)
            return response_builder._build_http_response(response)
        finally:
            close and close.close()

    @http.route(
        URL + "testing/" + "<identifier>",
        auth="public",
        type="http",
        webiste=True,
        methods=["POST"],
        csrf=False,
    )
    def test_handler(self, identifier, **post):
        threading.current_thread().testing = True
        return self._handler(identifier, **post)

    def _search_start(self, identifier, method):
        start_elements = request.env["zbs.start"].sudo()
        domain = [
            ("identifier", "=", str(identifier)),
        ]
        if method:
            domain += [
                # TODO otto - rest_config_id gibts hier nicht; nur wenn
                # rest modul auch installiert
                # ("rest_config_id.request_method", "=", str(method)),
                ("request_method", "=", str(method)),
            ]
        start_elements = start_elements.search(
            domain,
            limit=1,
            order="id desc",
        )
        return start_elements

    def create_instance(self, identifier, method, **post):
        assert identifier
        start_elements = self._search_start(identifier, method)
        if not start_elements:
            start_elements = self._search_start(identifier, method=None)
        if not start_elements:
            raise PipelineNotFoundException()
        data = {}
        if (
            request.httprequest.headers.get("Content-Type-orig") or ""
        ).lower() == "application/json" and request.httprequest.data:
            data = json.loads(request.httprequest.data)
        else:
            data = post
        authorization = start_elements.authorize_webrequest(
            headers=request.httprequest.headers, postdata=data, keyvalues=post
        )
        pipeline_line = (
            request.env["zbs.pipeline.line"]
            .sudo()
            .search([("worker_id", "=", f"{start_elements._name},{start_elements.id}")])
        )
        context = authorization.get("context", {})
        if start_elements.force_user_id:
            user = start_elements.force_user_id.id
        else:
            user = authorization["payload"]["odoo_user_id"]
        instance = (
            pipeline_line.pipeline_id.with_context(zbs_no_async_run=True, **context)
            .with_user(user)
            .start(data, no_cron_start=True, initiated_by="webcall")
        )

        return instance

    def run_instance(self, instance):
        try:
            instance.with_context(zbs_no_async_run=True)._start()
            instance._complete_run()
            instance.env.cr.commit()
            if instance.next_line_id.worker_id._name == "zbs.stop":
                response = instance._build_http_response()
            else:
                raise ZBSPipelineException(
                    code="OD500",
                    name="Pipeline Error",
                    msg=(
                        f"An error occured at instance {instance.id}, "
                        f"line {instance.next_line_id.id} "
                        f"worker-name {instance.next_line_id.worker_id._name}",
                    ),
                )
        except Exception as e:
            response = instance.env[
                "zbs.receiver.response.helper"
            ]._build_http_error_response(e, 500, "OD500")
        return response
