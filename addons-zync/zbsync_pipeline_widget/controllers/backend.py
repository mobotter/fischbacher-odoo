# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import http
from odoo.http import request


class Main(http.Controller):
    @http.route("/zync/change_sequence/<int:lineid>", auth="user", type="json")
    def _change_sequence(self, lineid, *args, dropped_on=None, **kwargs):

        dragged = request.env["zbs.pipeline.line"].browse(lineid)
        dropped = request.env["zbs.pipeline.line"].browse(int(dropped_on))

        lines = dropped.pipeline_id.line_ids.sorted()
        passed = False
        i = 1
        for line in lines:
            if passed:
                dragged.sequence = i
                i += 1
                passed = False

            if line == dropped:
                passed = True
            if line != dragged:
                line.sequence = i
            i += 1

        # fix stopper and start
        for line in lines.sorted():
            if line.worker_id._name == "zbs.start":
                line.sequence = -1
            elif line.worker_id._name == "zbs.stop":
                line.sequence = len(lines) * 2
        for i, line in enumerate(lines.sorted(), 1):
            line.sequence = i
