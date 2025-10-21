# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import http
from odoo.http import request
from odoo.http import content_disposition


class Controller(http.Controller):
    @http.route("/zync/transformer_helper/download", auth="user", type="http")
    def download_flows(self, **post):
        helper = request.env["zbs.transformer.helper"]
        str_ids = post["ids"]
        ids = map(int, str_ids.split(","))
        xml = helper._get_xml(ids)
        filename = f"helpers.xml"
        return http.request.make_response(
            xml,
            [
                ("Content-Type", "application/octet-stream; charset=binary"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )
