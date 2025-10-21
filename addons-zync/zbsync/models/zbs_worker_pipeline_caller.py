# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PipelineCaller(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.pipeline.caller"
    _description = "Start Other Pipeline"

    pipeline_id = fields.Many2one(
        "zbs.pipeline",
        string="Pipeline to Call",
        required=False,
        tracking=True,
        xport_rule="custom",
        xport_export="_xport_worker",
        xport_import="_import_worker",
    )
    mode = fields.Selection(
        [
            ("fire_and_forget", "Fire and Forget"),
            ("wait_until_done", "Wait Until Done"),
            ("return_data", "Return Data"),
        ]
    )
    call_mode = fields.Selection(
        [
            ("start_in_background", "Start in background"),
            ("start_and_execute", "Start and execute"),
        ],
        default="start_in_background",
    )
    extract_path = fields.Text(
        "Data Field",
        help="""Expected content: zSync Code
                Extract data from 'data' coming from previous pipeline-step and
                pass it to the sub-pipeline. To pass all write 'data'.""",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res["pipeline_id"] = False
        return res

    def _prepare_data(self, data):
        if self.extract_path:
            res = self.env["zbs.tools"]._exec_get_result(
                self.extract_path, {"data": data}
            )
        else:
            res = []
            for index, rec in self._iterate_data(data):
                res.append(rec)
        return self.env["zbs.tools"].zebrooset(res)

    def process(self, instance, data, errors=None):
        batch = self.env.context.get("zbs_batch")
        worker = self.env.context["zbs_pipeline"].worker_id
        if not self.pipeline_id:
            raise ValidationError("Pipeline not set")

        # first part
        if not batch.started_sub_instance_id:
            prepared_data = self._prepare_data(data)
            method = getattr(self.env["zbs.pipeline"], self.call_mode)
            sub_instance = method(
                name="", pipeline=self.pipeline_id, data=prepared_data
            )
            sub_instance.test_mode = instance.test_mode
            batch.started_sub_instance_id = sub_instance
            self.env["zbs.tools"].commit()
            if self.call_mode == "start_in_background":
                return instance.WaitHere()

        # second part
        sub_instance = batch.started_sub_instance_id
        result_data = data
        if self.mode == "wait_until_done":
            if sub_instance.state in ["success", "failed"]:
                return instance.Result(data)
            else:
                return instance.WaitHere()

        elif self.mode == "return_data":
            if sub_instance.state == "failed":
                raise Exception("Subpipeline aborted")
            elif sub_instance.state != "success":
                return instance.WaitHere()

            result_data = sub_instance._eval_data()
            for index, record in worker._iterate_data(data):
                for index2, record2 in worker._iterate_data(result_data):
                    if index == index2:
                        self._apply_keep_input(index, record, data, record2)

        return instance.Result(result_data)

    @api.model
    def _xport_worker(self, value):
        return {
            "name": self.pipeline_id.name,
            # do not name zync_uuid otherwise removing it at new import wont work
            "pipeline_uuid": self.pipeline_id.zync_uuid,
        }

    @api.model
    def _import_worker(self, value):
        uuid = value.get("pipeline_uuid")
        name = value.get("name")
        pipelines = self.env["zbs.pipeline"].search(
            ["|", ("zync_uuid", "=", uuid), ("name", "=", name)]
        )
        if not pipelines:
            raise ValueError(f"Could not find pipeline {name} {uuid}")
        return pipelines[0].id
