# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

import random
import base64
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from .zebrooset import ZebrooSet
from pathlib import Path
from ..exceptions import RetryableJobError
from ..exceptions import ZBSPipelineException
from ..exceptions import BatchFailed

try:
    from odoo.tools.safe_eval import wrap_module
except ImportError:
    from odoo.tools import wrap_module
import arrow
import logging

logger = logging.getLogger("zbs.zbs_instance")


class ZBSInstance(models.Model):
    _inherit = "mail.thread"
    _name = "zbs.instance"
    _description = "Zync Instance"
    _log_access = False
    _order = "id desc"

    has_subinstances = fields.Boolean(compute="_compute_has_subinstances")
    name = fields.Char("Name", required=True)
    environment_id = fields.Many2one("zbs.environment", "Environment")
    paused = fields.Boolean("Paused")
    effective_paused = fields.Boolean(
        compute="_effective_paused", store=False, readonly=True
    )
    create_date = fields.Datetime(default=lambda self: fields.Datetime.now())
    success_quote = fields.Integer("Success [%]")
    initial_data = fields.Text("Initial Data")
    origin = fields.Char("Origin")
    tag_ids = fields.Many2many("zbs.pipeline.tag", related="pipeline_id.tag_ids")
    next_line_id = fields.Many2one("zbs.instance.line", string="Current Line")
    prev_line_id = fields.Many2one("zbs.instance.line", compute="_compute_prev_line")
    following_line_id = fields.Many2one(
        "zbs.instance.line", compute="_compute_prev_line"
    )
    prev_line_override_id = fields.Many2one("zbs.instance.line")
    line_ids = fields.One2many("zbs.instance.line", "instance_id", string="Lines")
    pipeline_id = fields.Many2one(
        "zbs.pipeline",
        ondelete="cascade",
        required=True,
    )
    test_mode = fields.Boolean("Step-By-Step Mode", tracking=True)
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("running", "Running"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="pending",
        required=True,
        tracking=True,
    )
    is_main = fields.Boolean(
        "Is Main Run",
        default=True,
        help="If batched and splitted away, the children have false here; used to distinguish parallel runs",
    )
    date_start = fields.Datetime("Date Started", tracking=True)
    date_stop = fields.Datetime("Date Stopped", tracking=True)
    last_error = fields.Text("Last Error", compute="_compute_last_error")
    environment = fields.Text(
        "Environment Data",
        help="Basically a python dict that contains environmental data.",
    )
    last_heartbeat = fields.Datetime("Last Heartbeat", tracking=True)
    no_cron_start = fields.Boolean("Not processed in background", tracking=True)

    @property
    def dbstate(self):
        self.ensure_one()
        self.env.cr.execute("select state from zbs_instance where id = %s", (self.id,))
        rec = self.env.cr.fetchone()
        if not rec:
            return False
        return rec[0]

    def _set_state(self, state):
        self.env.cr.execute(
            "update zbs_instance set state = %s where id = %s", (state, self.id)
        )
        self.state = state

    @api.depends(
        "next_line_id",
        "next_line_id.batch_ids",
        "next_line_id.batch_ids.err_desc",
    )
    def _compute_last_error(self):
        for rec in self:

            def failed(x):
                return x.state == "failed"

            current_batches = rec.mapped("next_line_id.batch_ids").filtered(failed)
            prev_batches = rec.mapped("prev_line_id.batch_ids").filtered(failed)
            batches = current_batches or prev_batches
            errors = []
            for batch in batches:
                if batch.err_desc:
                    errors.append(f"Batch {batch.name}:")
                    errors.append(batch.err_desc)
            rec.last_error = "\n".join(errors)

    @api.constrains("next_line_id")
    def _check_next_line(self):
        for rec in self:
            if not rec.next_line_id:
                raise ValidationError("Next Line is required")

    def reset_current_line(self):
        line = self.next_line_id
        if not line:
            return
        line.make_current()

    def replay(self):
        prev_line = self.prev_line_id or self.next_line_id
        if prev_line:
            prev_line.make_current()
        self.heartbeat_ui()

    @api.model
    def _cron_gc_cleanup(self, *args, **kwargs):
        for pipeline in self.env["zbs.pipeline"].search([]):
            delta = timedelta(days=pipeline.keep_instances_for_days)
            crit = fields.Datetime.now() - delta
            states = ["success"]
            if pipeline.garbage_collect_failed_jobs:
                states.append("failed")
            for item in self.search(
                [
                    ("pipeline_id", "=", pipeline.id),
                    ("state", "in", states),
                    ("date_start", "<", crit),
                ]
            ):
                item.unlink()
                self.env["zbs.tools"].commit()

        self.env.cr.execute(
            """
            select id from zbs_instance_line where not exists(
                select 1 from zbs_instance where zbs_instance.id = zbs_instance_line.instance_id
            )
                            """
        )
        for id in self.env.cr.fetchall():
            self.env.cr.execute("delete from zbs_instance_line where id = %s", (id,))
            self.env["zbs.tools"].commit()

        self.env.cr.execute(
            """
            select id from zbs_instance_line_batch where not exists(
                select 1 from zbs_instance_line where zbs_instance_line.id = zbs_instance_line_batch.line_id
            )
                            """
        )
        for id in self.env.cr.fetchall():
            self.env.cr.execute(
                "delete from zbs_instance_line_batch where id = %s", (id,)
            )
            self.env["zbs.tools"].commit()

    @api.model
    def _cron_gc_vacuum(self, *args, **kwargs):
        for table in [
            "zbs_instance_line_batch",
            "zbs_instance_line",
            "zbs_instance",
        ]:
            self.env.cr.execute(f"commit;vacuum full {table};")

    def _zbs_message_post(self, *args, **kwargs):
        self.message_post(*args, **kwargs)

    @api.depends("next_line_id")
    def _compute_prev_line(self):
        for rec in self:
            if rec.prev_line_override_id:
                rec.prev_line_id = rec.prev_line_override_id.id
                continue

            # seen in V14
            # >>> rec.line_ids
            # zbs.instance.line(76, 77, 78)
            # >>> rec.line_ids.sorted()
            # zbs.instance.line()
            # >>> rec.line_ids
            # zbs.instance.line(76, 77, 78)
            lines = list(rec.line_ids.sorted(lambda x: x.sequence))
            if not rec.next_line_id:
                rec.prev_line_id = False
                continue
            try:
                index = lines.index(rec.next_line_id) - 1 if rec.next_line_id else -1
                fl_index = lines.index(rec.next_line_id) + 1 if rec.next_line_id else +1
            except ValueError:
                rec.prev_line_id = False
                rec.following_line_id = False
                continue
            if index < 0:
                rec.prev_line_id = False
            else:
                rec.prev_line_id = lines[index]
            if fl_index == 0:
                rec.following_line_id = False
            else:
                rec.following_line_id = lines[min(fl_index, len(lines) - 1)]

    def get_line_by_index(self, ix):
        lines = list(self.line_ids.sorted(lambda x: x.sequence))
        if ix > len(lines) - 1:
            return False
        return lines[ix]

    def get_line_index(self, line):
        lines = list(self.line_ids.sorted(lambda x: x.sequence))
        return lines.index(line)

    def _eval_data(self, force_line=None):
        if force_line is None:
            force_line = self.prev_line_id
        if not force_line or force_line.worker_id._name == "zbs.start":
            data = self.line_ids.load_data(self.initial_data)
        else:
            data = force_line._get_data()
        data = self._prepare_process_data(data)
        return data

    def _eval_exceptions(self):
        data = []
        for line in self.line_ids.sudo().sorted(reverse=True):
            if not line.generated_batches:
                continue
            data += line._get_errors()
        data = self._prepare_process_data(data)
        return data

    def WaitHere(self):
        from .zbs_batch import Wait

        return Wait()

    def Result(self, data, **kwargs):
        from .zbs_batch import ProcessResult

        return ProcessResult(data, **kwargs)

    def _filter_records(self, rec, the_range, ffilter):
        if not the_range and not ffilter:
            return rec

        def _applies_filter(item):
            bs = []

            for f in ffilter.split(","):
                f = f.strip()
                b = self.env["zbs.tools"]._exec_get_result(f, {"record": item})
                if not b:
                    return False
            return True

        if isinstance(rec, models.Model):
            instances = rec.browse()
            for i, record in enumerate(rec, 1):
                if self.next_line_id.isinrange(i, the_range):
                    instances |= rec
            if ffilter:
                instances = instances.filtered(_applies_filter)
            return instances

        rec2 = []
        for i, record in enumerate(rec, 1):
            if self.next_line_id.isinrange(i, the_range):
                if not ffilter or ffilter and _applies_filter(record):
                    rec2.append(record)
        return self.env["zebrooset"].rs(rec2)

    def _get_env(self):
        self.ensure_one()
        environment = self.environment or "{}"
        instance_env = self.env["zebrooset"].loads(environment or "{}")
        # To make it serializable for queuejobs (json dumps)
        return instance_env._d

    def _set_env(self, env):
        self.ensure_one()
        if not env:
            env = self.env["zebrooset"].loads("{}")
        if isinstance(env, dict):
            env = self.env["zebrooset"].rs(env)
        self.environment = env._dumps(env, env=self.env)

    def _get_default_objects(self, defaults):
        logger = logging.getLogger("zync")
        arrow2 = wrap_module(__import__("arrow"), ["get"])
        from ..exceptions import SkipRecord, ZBSPipelineException

        d = defaults
        d["ZBSPipelineException"] = ZBSPipelineException
        d["SkipRecord"] = SkipRecord

        d["SkipRecord"] = SkipRecord
        d.setdefault("datetime", datetime)
        d.setdefault("date", date)
        d.setdefault("timedelta", timedelta)
        d.setdefault("arrow", arrow2)
        d.setdefault("base64", base64)
        d.setdefault("Path", Path)
        d["env"] = self.env
        for k in ["zbs_instance_env"]:
            d[k] = self.env.context.get(k, d.get(k))
        d["zbs_instance_env"] = ZebrooSet(d["zbs_instance_env"] or {})
        d["instance_env"] = d["zbs_instance_env"]
        instance_line = self.env.context["zbs_pipeline"]
        d["instance_line"] = instance_line
        instance = self.env.context.get("zbs_instance")
        if instance_line:
            logger = logging.getLogger(f"zync.{instance.pipeline_id.name}")
            d["instance"] = instance
        d["initial_data"] = self.env.context.get("initial_data")
        d["logger"] = logger
        d["last_execution_date"] = (d["instance_env"] or {}).get(
            "last_execution_date", None
        )
        if not d["last_execution_date"]:
            d["last_execution_date"] = "1980-01-01 00:00:00"
        else:
            if isinstance(d["last_execution_date"], str):
                d["last_execution_date"] = arrow.get(d["last_execution_date"]).datetime
            d["last_execution_date"] = d["last_execution_date"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        def log(text, level="info"):
            pipeline = self.env.context.get("pipeline")
            if pipeline:
                pipeline.log(text, level)

        d["vars"] = self.env.context.get("zbs_variables")
        d["environment"] = self.env.context.get("zbs_environment")

        d["log"] = log
        return d

    def _check_running_count_and_prepare(self):
        self.state = "running"
        self.last_heartbeat = fields.Datetime.now()
        if not self.pipeline_id.limit_parallel_runs:
            return

        count_running = self.env["zbs.instance"].search_count(
            [
                ("pipeline_id", "=", self.pipeline_id.id),
                ("is_main", "=", True),
                ("test_mode", "=", False),
                ("state", "in", ["running"]),
                ("id", "<", self.id),
            ]
        )
        if count_running >= self.pipeline_id.limit_parallel_runs:
            if (
                not self.env["zbs.tools"]._is_testing()
                and not self.test_mode
                and not self.env.context.get("zbs_ignore_parallel_runs")
                and not self.env.context.get("heartbeat_ui")
            ):
                raise RetryableJobError(
                    f"Too many parallel jobs - allowed are {self.pipeline_id.limit_parallel_runs}",
                    seconds=random.randint(10, 30),
                    ignore_retry=True,
                )

    def _eval_path_content(self, pipeline, data, batchsize):
        result = []
        for batch_index, batchrec in self.env["zebrooset"].iterate(
            data, keep_small=True
        ):
            if any([x in pipeline.path_content for x in ["record", "batch"]]):
                result = []
                if not isinstance(batchrec._as_python_object(), list):
                    batchrec = [batchrec]
                for record_index, rec in self.env["zebrooset"].iterate(
                    batchrec, keep_small=True
                ):
                    recorditem = self.env["zbs.tools"]._exec_get_result(
                        pipeline.path_content, {"record": rec, "batch": rec}
                    )
                    dat = recorditem._as_python_object()
                    if isinstance(dat, list):
                        result += dat
                    else:
                        result.append(dat)
            else:
                result = self.env["zbs.tools"]._exec_get_result(
                    pipeline.path_content, {"data": batchrec}
                )
                try:
                    pt = result._as_python_object()
                except Exception as ex:
                    pt = result
                if not isinstance(pt, list):
                    result = [result]
        return self.env["zebrooset"].rs(result)

    def _make_batches(self, data, batchsize, can_commit=False):
        with self.env["zbs.tools"].pglock(f"{self._name}:{self.id}_batches"):
            self.ensure_one()

            pipeline = self.env.context["zbs_pipeline"]
            if pipeline.path_content:
                data = self._eval_path_content(pipeline, data, batchsize)

            data = self._filter_records(
                data, self.next_line_id.range, self.next_line_id.ffilter
            )
            # kill existing batches
            for batch in self.next_line_id.batch_ids:
                batch.unlink()
                if can_commit:
                    self.env["zbs.tools"].commit()
            for batch in self._make_batches_technical(data, batchsize):
                dumped = self.line_ids.dump_data(batch["batch"])
                self.next_line_id.batch_ids.create(
                    {
                        "line_id": self.next_line_id.id,
                        "state": "todo",
                        "start": batch["start"],
                        "stop": batch["stop"],
                        "length": batch["length"],
                        "input_data": dumped,
                    },
                )
                if can_commit:
                    self.env["zbs.tools"].commit()
            self.next_line_id.generated_batches = True
            if can_commit:
                self.env["zbs.tools"].commit()

    def _make_batches_technical(self, rs, batchsize):
        def yieldbatch(index, batch):
            return {
                "start": index,
                "batch": batch,
                "stop": index + len(batch),
                "length": len(batch),
            }

        batch = []
        if not batchsize:
            yield {
                "start": 0,
                "length": len(rs),
                "batch": rs,
                "stop": len(rs),
            }
        else:
            did_any, started = False, 0
            for index, rec in self.env["zebrooset"].iterate(rs, keep_small=True):
                did_any = True
                if len(batch) < batchsize:
                    batch.append(rec)
                else:
                    yield yieldbatch(started, batch)
                    batch = [rec]
                    started = index
            if batch or not did_any:
                yield yieldbatch(started, batch)

    def _prepare_process_data(self, input):
        if isinstance(input, models.Model):
            return input
        if input is None:
            # execute at least once if None is providing, indicating are start
            # A [] means, nothing to run, because no input given
            # 15.04.2024 web worker sends json={} if input is [{}]; a none should
            # stay a None
            input = [None]
        if not isinstance(input, (dict, list)) and not isinstance(input, ZebrooSet):
            input = [input]
        if isinstance(input, list):
            input = self.env["zebrooset"].rs(input)
        return input

    def _raise_retry(self, ex):
        raise RetryableJobError(
            "Serialize Error - retrying",
            seconds=10,
            ignore_retry=True,
        ) from ex

    def _do_continue_immediatley(self):
        if self.dbstate in ("failed", "success"):
            return False

        continue_immediately = True

        if self.test_mode:
            continue_immediately = False
        else:
            continue_immediately = self.next_line_id.continue_immediately

        return continue_immediately

    def _eval_fail_state(self):
        self = self.sudo()
        if not self._all_batches_done():
            return False
        faileds = any(
            x.state == "failed" for x in self.mapped("next_line_id.batch_ids")
        )

        all_count = len(self.line_ids.batch_ids)
        all_success = len(
            self.line_ids.batch_ids.filtered(lambda x: x.state == "success")
        )
        quote = float(all_success) / float(all_count) * 100 if all_count else 0
        self.success_quote = quote

        if faileds and self.next_line_id.abort_on_error:
            self._set_state("failed")

    def _goto_next_line(self):
        # all batches must be done:
        with self.env["zbs.tools"].pglock(f"{self._name}:{self.id}_gotonextline"):
            # check two times, could be changed by other process in meantime
            if self.dbstate == "failed":
                return False

            if not self._all_batches_done():
                return False

            self._eval_fail_state()

            if self.dbstate == "failed":
                return False

            next_line = self.next_line(self.next_line_id) or False
            if next_line:
                if next_line != self.next_line_id:
                    self.next_line_id = next_line
                next_line._reset_processed()
            else:
                self._set_state("success")
                self.date_stop = fields.Datetime.now()

    def _get_ui_context(self):
        return dict(
            zbs_ignore_parallel_runs=True,
            no_async_run=True,
            zbs_test_mode=True,
        )

    def heartbeat_ui(self):
        if self.dbstate == "failed":
            if not self.next_line_id.batch_ids or not any(
                x.state == "todo" for x in self.next_line_id.batch_ids
            ):
                self.next_line_id.make_current()

        if self.dbstate in ["success"]:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "information",
                    "message": "The instance is already on success",
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "soft_reload",
                    },
                },
            }
        self._set_state("running")
        self.env["zbs.tools"].commit()
        self = self.with_context(self._get_ui_context())
        try:
            self.heartbeat()
        except Exception as ex:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "warning",
                    "message": str(ex),
                    "next": {
                        "type": "ir.actions.client",
                        "tag": "soft_reload",
                    },
                },
            }
        return True

    def _needs_prepare_batches(self):
        self.ensure_one()

    def _build_batches(self, apply_continuation_group):
        self.ensure_one()
        # avoid dirty reads, that block later; cannot destroy advisory lock
        if apply_continuation_group:
            self._eval_continuation_group()
        self._check_running_count_and_prepare()
        pipeline_id = self.pipeline_id.id
        context = self._get_heartbeat_context()
        self.with_context(context)._ensure_batches(can_commit=True)
        return (
            self.mapped("next_line_id.batch_ids")
            .filtered(lambda x: x.state == "todo")
            .ids
        )

    def _get_heartbeat_context(self):
        self.ensure_one()
        debug_data = {
            "pipeline_name": self.pipeline_id.name,
            "zbs_line_name": self.name,
            "zbs_batchsize": self.next_line_id.batchsize
            or self.next_line_id.original_line_id.batchsize,
            "zbs_test_mode": self.env.context.get("zbs_test_mode") or self.test_mode,
            "zbs_pipeline": self.next_line_id,
            "zbs_instance": self,
            "zbs_environment": self._get_env(),
        }
        context = dict(self.env.context)
        for k, v in debug_data.items():
            context[k] = v
        return context

    @api.model
    def _is_using_queuejobs(self):
        return False

    def heartbeat(
        self,
        apply_continuation_group=False,
    ):
        """
        :apply_continuation_group: if set it is like a usual restart
            happened; in this case the instance continues at the restart group
            example:
            * you export data to another system which does not allow
        """
        self.env["zbs.tools"].cursor_change_to_read_committed()
        for rec in self:
            context = rec._get_heartbeat_context()
            testmode = self.env.context.get("zbs_test_mode") or rec.test_mode
            next_line_id = self.next_line_id.id
            no_async_run = self.env.context.get("zbs_no_async_run")
            if testmode:
                no_async_run = True
            del testmode

            if not self._is_using_queuejobs():
                no_async_run = True

            if self.env["zbs.tools"]._is_testing():
                no_async_run = True

            try:
                rec._make_and_queue_batches(
                    next_line_id,
                    context,
                    no_async_run,
                    apply_continuation_group,
                    commit_steps=True,
                )
            except Exception as ex:
                self._eval_fail_state()
                raise
            finally:
                self.env["zbs.tools"].commit()

    def _make_and_queue_batches(
        self,
        next_line_id,
        context,
        no_async_run,
        apply_continuation_group,
        commit_steps=False,
    ):
        self.ensure_one()
        assert isinstance(next_line_id, int), "next_line_id must be an int"
        next_line = self.next_line_id.browse(next_line_id)
        with self.env["zbs.tools"].pglock(f"{self._name}:{self.id}_make_batches"):
            if not next_line.generated_batches:
                batch_ids = self._build_batches(apply_continuation_group)
            else:
                batch_ids = next_line.batch_ids.ids
            batches = (
                self.env["zbs.instance.line.batch"].browse(batch_ids).read(["state"])
            )
            batch_ids = [x["id"] for x in batches if x["state"] == "todo"]

            # case batches exist - triggering later therefore
            for batch_id in batch_ids:
                try:
                    self._enqueue_batch(
                        batch_id,
                        allow_async=not no_async_run,
                        next_line_id=next_line_id,
                        heartbeat_context=context,
                        no_async_run=no_async_run,
                    )
                except RetryableJobError:
                    continue
                if commit_steps:
                    self.env["zbs.tools"].commit()

            continue_immediately = self._check_batchdone_continue()
            if continue_immediately:
                self._delay_instance(enabled=not no_async_run)

    def _all_batches_done(self):
        self.ensure_one()
        if not self.next_line_id.generated_batches:
            return False
        if not self.next_line_id.batch_ids:
            return True
        if any(x.state == "todo" for x in self.next_line_id.batch_ids):
            return False
        return True

    def _ensure_batches(self, can_commit=False):
        if self.next_line_id.generated_batches:
            return
        data = self._eval_data()
        batchsize = self.env.context["zbs_batchsize"]
        self._make_batches(data, batchsize=batchsize, can_commit=can_commit)

    @api.model_create_multi
    def create(self, vals_list):
        zenv = self.env["zbs.environment"].sudo()._get_default_env()
        for vals in vals_list:
            if "environment_id" not in vals:
                vals["environment_id"] = zenv.id
            pipeline = self.env["zbs.pipeline"].browse(vals["pipeline_id"])
            data = vals.get("data", None)
            if data:
                raise ValidationError(
                    "Please call _start method to start the instance with data."
                )
            vals["name"] = pipeline.sequence_id.next_by_id()
        res = super().create(vals_list)
        res._transfer_lines()
        start = res.line_ids.filtered(
            lambda x: x.worker_id and x.worker_id._name == "zbs.start"
        )
        if not start:
            raise ValidationError("Missing start element")

        return res

    def _transfer_lines(self):
        for line in self.pipeline_id.line_ids.filtered(lambda x: x.enabled):
            linevals = line._copy_for_instance(self)
            linevals["instance_id"] = self.id
            self.line_ids.create(linevals)

    @property
    def identity_key(self):
        self.ensure_one()
        return f"pipe#{self.pipeline_id.id}#instance#{self.id}"

    def _precheck_can_cron_heartbeat(self):
        return True

    @api.model
    def cron_heartbeat(self):
        for rec in self.search(
            [
                ("state", "in", ["pending", "running"]),
                ("paused", "=", False),
                ("pipeline_id.paused", "=", False),
                ("no_cron_start", "=", False),
            ],
            order="last_heartbeat desc",
        ):
            if not rec._precheck_can_cron_heartbeat():
                continue

            try:
                self.env["zbs.tools"].pg_advisory_lock(f"heartbeat_instance_{rec.id}")
            except RetryableJobError:
                continue

            try:
                rec._delay_instance(enabled=True)
            except RetryableJobError:
                continue
            # making queuejobs immediate visible
            self.env["zbs.tools"].commit()

    def _delay_instance(self, enabled=True):
        self.ensure_one()
        self.env["zbs.tools"].with_delay(
            self,
            enabled=enabled,
            identity_key=self.identity_key,
            channel=self.pipeline_id.queuejob_channel,
            priority=1,
        ).heartbeat(apply_continuation_group=True)

    def next_line(self, current_line):
        lines = self.with_context(active_test=False).line_ids.sorted()
        index = list(lines.ids).index(current_line.id)

        while True:
            if index + 1 >= len(lines):
                return None
            next_line = lines[index + 1]

            condition = None
            if next_line._has_condition_code():
                data = self._eval_data(force_line=current_line)
                condition = next_line._eval_condition(data)
            else:
                condition = True

            if condition:
                break
            index += 1

        return next_line

    def clear_messages(self):
        for rec in self:
            self.env["mail.message"].sudo().search(
                [("model", "=", self._name), ("res_id", "=", rec.id)]
            ).unlink()

    def retry(self):
        self.state = "running"

    def abort(self):
        self._set_state("failed")
        self.message_post(body="User aborted")

    def _eval_continuation_group(self):
        if not self.next_line_id.original_line_id.group_continue_here:
            return
        line = self.next_line_id
        group = line.original_line_id.group_continue_here
        while line._get_prev_line().original_line_id.group_continue_here == group:
            line = line._get_prev_line()

        if line != self.next_line_id:
            line.make_current()

    def _start(self):
        if self.next_line_id and self.next_line_id.continue_immediately:
            self.heartbeat()

    def goto_end(self):
        stopline = self.line_ids.filtered(lambda x: x.worker_id._name == "zbs.stop")
        self.prev_line_override_id = self.next_line_id
        self.next_line_id = stopline.id

    def where(self):
        if not self.next_line_id:
            return
        try:
            self.line_ids.ids.index(self.next_line_id.id)
        except ValueError:
            pass

    def _complete_run(self):

        while self.dbstate in ["pending", "running"]:
            self.where()
            self.with_context(zbs_no_async_run=True).heartbeat()
        return self

    def _build_http_response(self):
        if not self.next_line_id.worker_id.return_data:
            data = []
        else:
            data = self._eval_data()
            data = self.env["zebrooset"].get_python_type(data)

        return {
            "body": data,
            "headers": {
                "Content-Type": self.next_line_id.worker_id.content_type
                or "application/json"
            },
            "http_status_code": 200,
        }

    def _enqueue_batch(
        self,
        batch_id,
        allow_async=True,
        next_line_id=None,
        heartbeat_context=None,
        no_async_run=None,
    ):
        self.env["zbs.tools"].pg_assert_read_committed()
        next_line_id = next_line_id or self.next_line_id.id
        nl = self.env["zbs.instance.line"].browse(next_line_id)
        queuejob_channel = (
            nl.original_line_id.queuejob_channel or self.pipeline_id.queuejob_channel
        )
        queuejob_priority = (
            nl.original_line_id.queuejob_priority or self.pipeline_id.queuejob_priority
        )
        context = heartbeat_context or self._get_heartbeat_context()
        context_batch = dict(context.items())
        context_batch.update(
            {
                "zbs_instance_id": self.id,
                "zbs_pipeline_id": next_line_id,
                "zbs_instance": None,
                "zbs_pipeline": None,
            }
        )
        # TODO check if context is persisted

        idkey = f"zbs_batch_{batch_id}"
        self.env["zbs.tools"].with_context(context_batch).with_delay(
            self.env["zbs.instance.line.batch"]
            .browse(batch_id)
            .with_context(context_batch),
            enabled=allow_async,
            identity_key=idkey,
            priority=queuejob_priority,
            channel=queuejob_channel,
        ).heartbeat(batch_id, context_batch, no_async_run=no_async_run)

    def _check_batchdone_continue(self):
        self.env["zbs.tools"].pg_assert_read_committed()
        with self.env["zbs.tools"].pglock(f"{self._name}:{self.id}_checkdone"):
            self = self.sudo()
            continue_immediately = False
            if not self.exists():
                return continue_immediately
            self._eval_fail_state()
            if self._all_batches_done():
                self._goto_next_line()
                if self._do_continue_immediatley():
                    continue_immediately = True

            return continue_immediately

    @api.depends("pipeline_id.paused", "paused")
    def _effective_paused(self):
        for rec in self:
            rec.effective_paused = rec.paused or rec.pipeline_id.paused

    def _raise_for_status(self, for_user=False):
        if self.dbstate not in ["failed"]:
            return

        if not self._all_batches_done():
            return
        exceptions = self._eval_exceptions()
        if not exceptions:
            return

        try:
            name = self.name
            current_step = self.next_line_id.name
            current_mapper = self.next_line_id.worker_id._description
            msg = f"Pipeline Step failed: #{name} at {current_step} ({current_mapper})"
            if len(exceptions) > 0:
                msg += "\n" + msg[0]
            raise ZBSPipelineException(
                code=None,
                name=msg,
                error_records=exceptions,
            )
        except Exception as ex:
            if for_user:
                raise UserError(str(ex)) from ex
            raise

    def _roll_after_start(self):
        self.env["zbs.tools"].cursor_change_to_read_committed()
        if self.next_line_id.continue_immediately:
            self.no_cron_start = True
            self.env["zbs.tools"].commit()
            self.env.clear()

            def raiseup():
                raise UserError(self.last_error) from ex

            try:
                self._complete_run()
            except BatchFailed as ex:
                raiseup()

            if self.next_line_id.worker_id._name != "zbs.stop" and self.last_error:
                raiseup()

            self.env.clear()
            self.env["zbs.tools"].commit()
            self._raise_for_status()

            self.env["zbs.tools"].commit()
            self.no_cron_start = False
            self.env["zbs.tools"].commit()

        else:
            self.no_cron_start = False
            self.env["zbs.tools"].commit()

    def open_sub_instances(self):
        ids = self.line_ids.batch_ids.started_sub_instance_id.ids
        return {
            "name": f"Subinstances of {self.name} {self.pipeline_id.name}",
            "view_type": "form",
            "res_model": self._name,
            "domain": [("id", "in", ids)],
            "views": [(False, "list"), (False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def _compute_has_subinstances(self):
        for rec in self:
            rec.has_subinstances = bool(rec.line_ids.batch_ids.started_sub_instance_id)
