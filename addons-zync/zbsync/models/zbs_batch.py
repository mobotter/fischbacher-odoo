# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import api, fields, models, SUPERUSER_ID
import psycopg2
from odoo import api, fields, models
from ..exceptions import RetryableJobError
from .zebrooset import ZebrooSet, _WrappedList
import traceback
import logging
import random
from contextlib import contextmanager
from ..exceptions import BatchFailed, RetryInNextTimeframe

LOCK_SEPARATOR = ":::::"

logger = logging.getLogger("zbs.batch")


class CounterTable(models.Model):
    _name = "zbs.batch.counter"
    _description = "Zync Batch Counter"
    _log_access = False

    batch_id = fields.Many2one(
        "zbs.instance.line.batch", ondelete="cascade", required=True, index=True
    )
    amount = fields.Integer("Count", default=0)


class ProcessResult(object):
    def __init__(self, data, after_commit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = data
        self.after_commit = after_commit


class Wait(ProcessResult):
    def __init__(self, *args, **kwargs):
        super().__init__(data=None, *args, **kwargs)


class Batch(models.Model):
    _name = "zbs.instance.line.batch"
    _description = "Zync Batch"
    _order = "id"
    _log_access = False

    how_to_debug = fields.Char(compute="_compute_how_to_debug")
    create_date = fields.Datetime(default=lambda self: fields.Datetime.now())
    name = fields.Char(string="Name", compute="_compute_name")
    start = fields.Integer("Start")
    stop = fields.Integer("Stop")
    length = fields.Integer("Length")
    line_id = fields.Many2one(
        "zbs.instance.line",
        string="Line",
        readonly=True,
        store=True,
        index=True,
        ondelete="cascade",
    )
    worker_id = fields.Reference(
        related="line_id.worker_id",
        store=True,
    )
    instance_id = fields.Many2one(
        "zbs.instance",
        related="line_id.instance_id",
        readonly=True,
        store=True,
        index=True,
    )
    state = fields.Selection(
        [("todo", "Todo"), ("success", "Success"), ("failed", "Failed")],
        string="State",
        default="todo",
        required=True,
        tracking=True,
    )
    err_desc = fields.Text("Error")

    input_data = fields.Text("Input Data")
    output_data = fields.Text("Output Data")
    processed_records = fields.Integer("Processed Records", compute="_compute_counter")
    done_tries = fields.Integer("Done Tries", tracking=True, readonly=True)
    log_ids = fields.One2many(
        "zbs.instance.logs", "batch_id", string="Logs", copy=False
    )
    started = fields.Datetime()
    stopped = fields.Datetime()
    duration = fields.Float("Duration [s]")
    started_sub_instance_id = fields.Many2one("zbs.instance", readonly=True)
    locked_resources = fields.Text("Locked Resources")

    def show_data(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/zync/batch/data/{self.id}",
            "target": "new",
        }

    def _compute_name(self):
        for rec in self:
            parent_name = rec.line_id.name
            rec.name = "-".join(filter(bool, [parent_name, rec.uistring]))

    @property
    def uistring(self):
        return f"{self.start} - {self.stop}: {self.state}"

    def _get_exceptions(self):
        data = self.err_desc or []
        data = self.env["zbs.instance.line"].load_data(data)
        if data is None:
            data = [None]
        elif hasattr(data, "_as_python_object") and not isinstance(
            data._as_python_object(), list
        ):
            data = [data._as_python_object()]
        else:
            data = [data]

        return self.env["zebrooset"].rs(data)

    def _get_data(self):
        data = self.output_data or []
        data = self.env["zbs.instance.line"].load_data(data)
        return data

    def _inc_processed(self, qty=1):
        for rec in self:
            self.env.cr.execute(
                "INSERT INTO zbs_batch_counter" "(batch_id, amount) " "VALUES(%s, %s)",
                (rec.id, qty),
            )

    def _compute_counter(self):
        with self.env["zbs.tools"].new_env() as env:
            env["zbs.tools"].cursor_change_to_read_committed()
            env.cr.execute(
                "select sum(amount), batch_id "
                "from zbs_batch_counter "
                "where batch_id in %s "
                "group by batch_id ",
                (tuple(self.ids),),
            )
            counts = env.cr.fetchall()

        for rec in self:
            db = [x for x in counts if x[1] == rec.id]
            if not db:
                count = 0
            else:
                count = db[0][0] or 0
            rec.processed_records = count

    def open_logs(self):
        self.ensure_one()
        logs = self.log_ids
        if not logs:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Logs",
            "res_model": logs._name,
            "res_id": logs[0].id,
            "views": [(False, "form")],
            "target": "new",
            "flags": {
                "form": {
                    "action_buttons": False,
                    "initial_mode": "view",
                }
            },
        }

    def _log_process_result(self, started, process_result):
        if not process_result:
            return
        output_data = (
            self.env["zbs.instance.line"].sudo().dump_data(process_result.data)
        )
        self.log_ids.sudo().create(
            {
                "date_start": started,
                "date_stop": fields.Datetime.now(),
                "batch_id": self.id,
                "output_data": output_data,
            }
        )
        self.output_data = output_data
        self.line_id.log(str(process_result.data), "debug")

    def heartbeat_ui(self):
        self.env["zbs.tools"].cursor_change_to_read_committed()
        for rec in self:
            rec.state = "todo"
            rec.err_desc = False
            rec.line_id.instance_id.state = "running"
            assert rec.state == "todo", (
                "State should now be todo, but is %s" % rec.state
            )
            self.env["zbs.tools"].commit()
            rec.line_id.instance_id.with_context(
                zbs_noasync_run=True,
            )._enqueue_batch(rec.id, allow_async=False, no_async_run=True)
        return True

    @api.model
    def advisory_lock_name(self, batch_id):
        return f"{self._name}:{batch_id}"

    @api.model
    def heartbeat(self, batch_id, context, no_async_run):
        started = fields.Datetime.now()
        self = self.browse(batch_id).with_context(context)
        self.env["zbs.tools"].cursor_change_to_read_committed()
        if not self.exists():
            return

        if self.line_id.instance_id.state == "failed":
            return
        retry_in_nextround = False

        self.env["zbs.tools"].commit()
        if not self.check_state_todo():
            return

        Tools = self.env["zbs.tools"]

        self = self.sudo()

        with Tools.pglock(f"batch_{self.instance_id.id}/{self.id}"):
            with self._clearance_granted() as (data, errors):
                try:
                    # in _exec_run commits are happening; they destroy any locks
                    # from clearance_granted; but is ok: after exec_run only states
                    # have to be written
                    result = self._exec_run(data, errors=errors)
                    count_records = self._eval_processed(result.data)
                    self._inc_processed(count_records)
                    self.state = "success"
                    self._calc_duration(started)
                except (
                    psycopg2.errors.InFailedSqlTransaction,
                    psycopg2.errors.SerializationFailure,
                ) as ex:
                    msg = traceback.format_exc()
                    raise RetryableJobError(
                        "Serialize Error - retrying\nTraceback:\n" + msg,
                        ignore_retry=True,
                        seconds=random.randint(2, 60),
                    ) from ex
                except BatchFailed as ex:
                    self.instance_id._eval_fail_state()
                    Tools.commit()
                    raise
                except RetryInNextTimeframe:
                    retry_in_nextround = True

            if not self.exists():
                return

            instance = self.line_id.instance_id
            if retry_in_nextround:
                no_async_run = False
            Tools.commit()

        Tools.cursor_change_to_read_committed()
        continue_immediatley = instance._check_batchdone_continue()

        if (continue_immediatley) and (not self.env["zbs.tools"]._is_testing()):
            instance._delay_instance(enabled=not no_async_run)
        Tools.commit()

    @contextmanager
    def _clearance_granted(self):

        def _get_data():
            data = self.env["zbs.instance.line"].load_data(self.input_data)
            errors = self.line_id.instance_id._eval_exceptions()

            return data, errors

        if self.line_id.original_line_id.batch_execution_in_order:
            self.retry_if_batch_execution_in_order()

        locks = [self.advisory_lock_name(self.id)]
        if self.line_id.worker_id.can_lock_resources:
            with self.env["zbs.tools"].pglock(
                f"resoure_check_{self.line_id.id}", wait=True
            ):
                data, errors = _get_data()
                self._identify_worker_locks(data, errors=errors)
                locks += self._extract_locks()
        data, errors = _get_data()
        with self.env["zbs.tools"].pglock(locks):
            yield data, errors

    def check_state_todo(self):
        self.env.cr.execute(
            f"select state from {self._table} where id =%s",
            (self.id,),
        )
        dbbatch = self.env.cr.fetchone()
        if dbbatch is None:
            # Batch does not exist anymore
            return False
        state = dbbatch[0]
        return state == "todo"

    def _identify_worker_locks(self, data, errors):
        """
        Let the worker calculate resource locks

        """
        locks = self._exec_run(data, errors=errors, dry_run_get_locks=True)
        locks = LOCK_SEPARATOR.join(map(str, locks))

        self.locked_resources = locks

    def _extract_locks(self):
        return list(filter(bool, (self.locked_resources or "").split(LOCK_SEPARATOR)))

    def _calc_duration(self, started):
        self.ensure_one()
        self.duration = 0
        self.started = started
        self.stopped = fields.Datetime.now()
        if self.started and self.stopped:
            self.duration = (self.stopped - self.started).total_seconds()

    def _eval_processed(self, array):
        if isinstance(array, ZebrooSet):
            counter = 0
            for _, _ in array._iterate_records():
                counter += 1
            return counter
        if isinstance(array, _WrappedList):
            return len(array._l)
        if isinstance(array, (list, tuple)):
            return len(array)
        if array:
            return 1
        return 0

    def _exec_run(self, data, errors, dry_run_get_locks=None):
        self.env["zbs.tools"].pg_assert_read_committed()
        with self.env["zbs.tools"].pglock(f"exec_run_{self.id}"):
            self.ensure_one()
            started = fields.Datetime.now()

            try:
                instance = self.line_id.instance_id
                pipeline = self.line_id
                instance_env = instance._get_env()
                instance = instance.with_context(instance_env=instance_env)
                context = {}
                for k, v in self.env.context.items():
                    context[k] = v
                context.update(
                    dict(
                        zbs_pipeline=pipeline,
                        zbs_instance=instance,
                        zbs_batch=self,
                        keep_input_filter=self.line_id.keep_input_filter,
                    )
                )
                # re-update the context
                instance = instance.with_context(context)
                context["zbs_batch_id"] = self.id
                context["zbs_instance"] = instance
                context["zbs_instance_env"] = instance_env
                context["zbs_environment"] = (
                    self.env["zbs.variable"].sudo()._get_values(instance.environment_id)
                )
                self._cachings(context, data)
            except Exception as ex:
                logger.error(
                    f"Exception at preparation of batch-run {self.id} of instance {instance.id}",
                    exc_info=True,
                )
                raise RetryableJobError(
                    str(ex), ignore_retry=True, seconds=random.randint(1, 8)
                ) from ex

            worker = self.line_id.worker_id.with_context(context)
            with self.env["zbs.tools"].new_env(enabled=True) as worker_env:
                was_sudo = self.env.su
                if self.env.user.id != SUPERUSER_ID:
                    # queuejobs is sudoing the env; remove that
                    if self.env.su:
                        self = self.sudo(False)
                        assert not self.env.su

                worker = worker.with_env(worker_env).with_context(context)
                try:
                    if dry_run_get_locks:
                        result = worker.get_lock_resources(
                            instance, data, errors=errors
                        )
                    else:
                        result = worker.process(instance, data, errors=errors)
                except (
                    psycopg2.errors.InFailedSqlTransaction,
                    psycopg2.errors.SerializationFailure,
                ):
                    self = self.sudo()
                    logger.error(
                        f"Serializable or failed transaction error at batch {self.id} of instance {instance.id}",
                        exc_info=True,
                    )
                    raise
                except RetryableJobError:
                    self = self.sudo()
                    logger.error(
                        f"Retryable job error at batch {self.id} of instance {instance.id}"
                    )
                    raise
                except Exception as ex:
                    self = self.sudo()
                    logger.error(
                        f"Exception at batch {self.id} of instance {instance.id}",
                        exc_info=True,
                    )
                    self.sudo()._handle_exception(ex, started)
                    raise BatchFailed(str(ex)) from ex
                else:
                    self = self.sudo(was_sudo)
                    instance._set_env(context["zbs_instance_env"])

                    if not dry_run_get_locks:
                        if isinstance(result, Wait):
                            raise RetryInNextTimeframe()

                if not dry_run_get_locks:
                    try:
                        worker._do_post_process(result)
                        instance._set_env(context["zbs_instance_env"])

                        result = self._eval_bare_process_result(result)
                        self._log_process_result(started, result)
                    except Exception as ex:
                        logger.error(
                            f"Exception at batch {self.id} of instance {instance.id}",
                            exc_info=True,
                        )
                        self.sudo()._handle_exception(ex, started)
                        raise BatchFailed(str(ex)) from ex

                if not dry_run_get_locks:
                    worker.env["zbs.tools"].commit()
                    if result and result.after_commit:
                        result.after_commit()
                        worker.env["zbs.tools"].commit()

            return result

    def _cachings(self, context, data):
        self.ensure_one()
        if context.get("zbs_instance"):
            instance = context["zbs_instance"]
            initial_data = self.line_id.load_data(instance.initial_data)
            context["initial_data"] = initial_data
            context["zbs_variables"] = (
                self.env["zbs.variable"].sudo()._get_values(instance.environment_id)
            )
        context["zbs_prepared_input_data"] = (
            self.env["zebrooset"].rs(data) if isinstance(data, (dict, list)) else data
        )

    def _eval_bare_process_result(self, res):
        if res and not isinstance(res, ProcessResult):
            raise Exception(f"Expected type process result for {res}")
        process_result = res
        return process_result

    def _handle_exception(self, ex, started):
        pipeline_name = self.env.context["pipeline_name"]
        zbs_line_name = self.env.context["zbs_line_name"]
        logger.error(
            f"{pipeline_name}-{zbs_line_name}",
            exc_info=True,
        )
        try:
            self.env["zbs.tools"].commit()
            if not self.env["zbs.tools"]._is_testing():
                self.env.clear()
        except psycopg2.errors.InterfaceError:
            logger.error("Process seems to forcibly killed - no rollback required")
        try:
            # we are in easy read_committed transaction
            self._set_failed(ex=ex)
            self.log_ids.create(
                {
                    "batch_id": self.id,
                    "date_start": started,
                    "date_stop": fields.Datetime.now(),
                    "last_exception": self.env["zbs.exception.formatter"].as_json(ex),
                }
            )
        except Exception as ex:
            logger.error(str(ex), exc_info=True)

    def _set_failed(self, ex=None):
        pattern = self.line_id.original_line_id.retry_pattern or ""
        for rec in self:
            if pattern:
                pattern = list(map(lambda x: int(x.strip()), pattern.split(",")))
                if self.done_tries < len(pattern):
                    rec.done_tries += 1
                    rec.env["zbs.tools"].commit()
                    raise RetryableJobError(
                        ignore_retry=True, seconds=pattern[rec.done_tries]
                    )
            rec.state = "failed"
            rec.done_tries += 1
            if ex:
                rec.err_desc = self.env["zbs.exception.formatter"].as_json(ex)

            rec.env["zbs.tools"].commit()

    def _get_worker_selection(self):
        return self.env["zbs.worker"].zbs_sub_classes_for_selection()

    def _compute_how_to_debug(self):
        for rec in self:
            rec.how_to_debug = f"env['{self._name}'].browse({self.id})._debug_play()"

    def _debug_play(self):
        self.state = "todo"
        self.env.cr.commit()
        self.instance_id._enqueue_batch(
            self.id,
            allow_async=False,
            next_line_id=self.line_id.id,
            heartbeat_context={},
            no_async_run=True,
        )

    def unlink(self):
        for rec in self:
            if rec.started_sub_instance_id:
                rec.started_sub_instance_id.unlink()
        return super().unlink()

    @api.model
    def retry_if_batch_execution_in_order(self, instance_line_id):
        self.env.cr.execute(
            f"""
            select exists(
            select
            from {self._table}
            where line_id = %s
            and state = 'todo'
            and id < %s
            limit 1
            )""",
            (self.line_id.id, self.id),
        )
        next_batch = self.env.cr.fetchone()
        if next_batch and next_batch[0] != self.id:
            raise RetryableJobError(
                "Batch has to wait for previous batches.",
                ignore_retry=True,
                seconds=random.randint(10, 120),
            )
