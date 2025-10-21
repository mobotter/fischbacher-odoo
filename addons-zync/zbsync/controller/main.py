# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

import json
from odoo import http
from odoo.http import request


class Main(http.Controller):
    @http.route("/zync_download_version/<int:id>", auth="user", type="http")
    def handler(self, id, **post):
        version = request.env["zbs.pipeline.version"].browse(id)
        res = version.content
        name = f"{version.pipeline_id.name}.{version.date}.json"
        return http.request.make_response(
            res,
            [
                ("Content-Type", "application/json"),
                ("Content-Disposition", f'attachment; filename="{name}"'),
            ],
        )

    @http.route("/zync/instance_line/data/<int:id>", auth="user", type="http")
    def show_instance_line_data(self, id):
        line = request.env["zbs.instance.line"].browse(id)
        data = line._get_data()
        return self._show_data(data)

    def _show_data(self, data):
        is_json = False
        if hasattr(data, "_dumps"):
            data = data._dumps(data, env=request.env)
            is_json = True
        else:
            try:
                data = json.dumps(data, indent=4)
                is_json = True
            except:
                data = str(data)

        if is_json:
            html = request.env["ir.ui.view"]._render_template(
                "zbsync.jsonviewer",
                values={
                    "data": data,
                },
            )
        else:
            html = str(data)
        return http.request.make_response(
            html,
            [
                ("Content-Type", "text/html"),
            ],
        )
