# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import http
from odoo.http import request
from odoo.http import content_disposition


class Controller(http.Controller):
    @http.route("/zync/download", auth="user", type="http")
    def download_flows(self, **post):
        str_ids = post["ids"]
        ids = map(int, str_ids.split(","))
        pipes = request.env["zbs.pipeline"].browse(ids)
        zip = pipes._get_zipped_json()
        filename = f"pipes_{str_ids}.zip"
        return http.request.make_response(
            zip,
            [
                ("Content-Type", "application/octet-stream; charset=binary"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )
