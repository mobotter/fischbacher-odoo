from functools import partial
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.sql import table_exists
from odoo.tools.safe_eval import safe_eval
import inspect
from collections import defaultdict
import logging
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger("method_hook.trigger")


class TriggerMethodHook(models.AbstractModel):
    _name = "method_hook.trigger.mixin"
    _description = "Method-based Trigger"

    domain = fields.Char("Domain", required=True, default="[]")
    method = fields.Char("Method", required=True, help="e.g. create,write")
    model_name = fields.Char(related="model_id.model", string="Model Name")
    enabled = fields.Boolean(default=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
    )
    link_expression = fields.Char("Link Expression", default="object")

    def _trigger(self, instances, args_packed, method):
        raise NotImplementedError("Implement hook!")

    def _eval_linkexpression(self, object):
        object = object.sudo()
        if not self.link_expression:
            return object
        recs = safe_eval(
            self.link_expression,
            dict(obj=object, object=object, objects=object, env=self.env),
        )
        return recs

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        result._check_method()
        result._update_registry()
        return result

    def write(self, vals):
        result = super().write(vals)
        self._check_method()
        self._update_registry()
        return result

    def unlink(self):
        result = super().unlink()
        self._update_registry()
        return result

    @api.constrains("method")
    def _check_method(self):
        for rec in self:
            if not rec.method:
                continue
            obj = self.env.get(rec.model_id.model)
            if obj is None:
                raise ValidationError((f"Object not found: {rec.model_id.model}."))
            for method in rec._split_methods():
                if not getattr(obj, method, None):
                    raise ValidationError(
                        (f"Could not find {method} on {rec.model_id.model}.")
                    )

    def _split_methods(self):
        self.ensure_one()
        return list(map(lambda x: x.strip(), self.method.split(",")))

    @api.model
    def _update_registry(self):
        self.pool.registry_invalidated = True
        self.pool.signal_changes()
        self._register_hook()

    def _register_hook(self):
        if (
            not table_exists(self.env.cr, self._table)
            or self._name == "method_hook.trigger.mixin"
        ):
            return

        def make_hook(trigger_model, obj, model_id, method, _def, filters=None):
            """Instanciate a create method that processes action rules."""

            method_name = method
            assert isinstance(method_name, str)

            def is_model_function():
                # TODO: __wrapped__ not set
                # surely better way to retrieve @api.model situation
                # https://stackoverflow.com/questions/43506378/how-to-get-source-code-of-function-that-is-wrapped-by-a-decorator
                func = getattr(obj, method)
                src = inspect.getsource(func).split("def")[0]
                return "@api.model" in src

            def _pack_args(args, kwargs):
                return {"args": args, "kwargs": kwargs}

            # Make sure that for write and create the first argument is always
            # the vals (not kwargs), so that all that depend on this have the
            # same interface

            @api.model_create_multi
            def patched_create(self, vals_list, **kw):
                result = patched_create.origin(self, vals_list, **kw)
                for i, record in enumerate(result):
                    vals = vals_list[i]
                    _def(record, method_name, _pack_args([vals], kw))
                return result

            def patched_write(self, vals, **kwargs):
                # must be set before the write to have old value in db
                # and write values in vals
                old_vals = {}

                hook_filter = filters
                if hook_filter:
                    assert isinstance(hook_filter, list)
                    if isinstance(hook_filter, list) and len(hook_filter) > 1:
                        raise NotImplementedError(hook_filter)
                    if isinstance(hook_filter, list):
                        hook_filter = hook_filter[0]
                filter_event, filter_fieldnames = None, None
                if isinstance(hook_filter, dict):
                    filter_event = hook_filter.get("event")
                    filter_fieldnames = hook_filter.get("fieldname")
                else:
                    raise NotImplementedError(hook_filter)

                for record in self:
                    if filter_event == "before.write":
                        kwargs["trigger.filters"] = "before.write"
                        _def(record, method_name, _pack_args([vals], kwargs))
                        kwargs.pop("trigger.filters")
                    if filter_fieldnames and any(x in filter_fieldnames for x in vals):
                        old_vals[record.id] = record.read(fields=filter_fieldnames)[0]
                result = patched_write.origin(self, vals, **kwargs)
                for record in self:
                    if not filter_event or filter_event == "after.write":
                        kwargs["trigger.filters"] = "after.write"
                        if record.id in old_vals:
                            kwargs["old"] = old_vals[record.id]
                        _def(record, method_name, _pack_args([vals], kwargs))
                return result

            @api.model
            def patched_model(self, *args, **kwargs):
                result = patched_model.origin(self, *args, **kwargs)
                _def(self, method_name, _pack_args(args, kwargs))
                return result

            def patched(self, *args, **kwargs):
                result = patched.origin(self, *args, **kwargs)
                _def(self, method_name, _pack_args(args, kwargs))
                return result

            if method == "create":
                return patched_create
            elif method == "write":
                return patched_write
            elif is_model_function():
                return patched_model
            else:
                return patched

        patched_funcs = defaultdict(set)

        def patch(obj, method_name, method, hook_id):
            """Patch method `name` on `model`, unless it has been patched already."""

            key = f"{method_name}#hook#{hook_id}"
            if key not in patched_funcs[key]:
                patched_funcs[key].add(obj._name)
                obj._patch_method(method_name, method)

        # retrieve all actions, and patch their corresponding model
        self._activate_hooks(patch, make_hook)

    def _check_obj_exists(self, obj, model):
        # Do not crash if the model of the base_action_rule was uninstalled
        if obj is None:
            _logger.warning(
                (f"Check Method with ID {model.id} depends " f"on model {model.model} ")
            )
            return False
        return True

    def _trigger_prepare(self, recordset, args_packed, func):
        if not self.exists():
            return
        domain = safe_eval(self.domain)
        if domain:
            recordset = recordset.filtered_domain(domain)
        for rec in recordset:
            rec = rec.sudo()
            linkedrecords = self._eval_linkexpression(rec)
            for linkedrecord in linkedrecords:
                func(linkedrecord)

    def _activate_hooks(self, patch, make_hook):
        for hook in self.sudo().search([("enabled", "=", True)]):
            obj = self.env.get(hook.model_id.model)

            if not self._check_obj_exists(obj, hook.model_id):
                continue

            def _trigger_hook(hook, recordset, method_name, args_packed):
                new_hook = hook.with_env(recordset.env).sudo()
                filters = args_packed.get("kwargs", {}).get("trigger.filters")
                if filters and filters == "before.write":
                    return
                if not new_hook.exists():
                    return
                if new_hook.model_id.model != recordset._name:
                    return
                for method in new_hook._split_methods():
                    if method != method_name:
                        continue
                    new_hook._trigger_prepare(
                        recordset,
                        args_packed,
                        lambda linkedrecord: new_hook._trigger(
                            linkedrecord, args_packed, method
                        ),
                    )

            for method in hook._split_methods():
                _trigger_hook = partial(_trigger_hook, hook)
                if getattr(obj, method, None):
                    patch(
                        obj,
                        method,
                        make_hook(
                            self._name,
                            obj,
                            hook.model_id.id,
                            method,
                            _trigger_hook,
                            filters=[{"event": "after.write"}],
                        ),
                        hook.id,
                    )
