# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class PipelineLine(models.Model):
    _inherit = "zbs.instance.line"

    def compute_rendercontent(self):
        res = self.original_line_id.compute_rendercontent()
        res["line"]["model"] = self._name
        res["line"]["id"] = self.id
        res["line"]["is_current"] = self.instance_id.next_line_id == self
        res["line"]["can_set_as_next_line"] = self.instance_id.next_line_id != self
        res["line"]["is_instance"] = True
        res["line"]["instance_line_id"] = self.id
        res["line"]["instance_id"] = self.instance_id.id
        res["line"]["range"] = self.range
        res["line"]["output_range"] = self.output_range
        res["line"]["ffilter"] = self.ffilter
        res["line"]["output_ffilter"] = self.output_ffilter
        res["line"]["batchsize"] = self.batchsize

        res["line"]["batches"] = []

        self.env.cr.execute(
            """
            select count(*), state, sum(length) as length
            from zbs_instance_line_batch
            where line_id=%s
            group by state
            order by state
        """,
            (self.id,),
        )

        res["line"]["batches"] = []
        for batchsum in self.env.cr.fetchall():
            res["line"]["batches"].append(
                {
                    "length": batchsum[2],
                    "count": batchsum[0],
                    "state": batchsum[1],
                    "line_id": self.id,
                }
            )

        return res
