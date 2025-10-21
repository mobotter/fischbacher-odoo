# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import http


class ZSyncDispatcher(http.HttpDispatcher):
    routing_type = "zync"

    def dispatch(self, endpoint, args):
        headers = dict(self.request.httprequest.headers)
        if headers.get("Content-Type") == "application/json":
            headers["Content-Type"] = "text/json"
            headers["Content-Type-orig"] = "application/json"
            self.request.httprequest.headers = headers
        res = super().dispatch(endpoint, args)
        return res

    @classmethod
    def is_compatible_with(cls, request):
        return True
