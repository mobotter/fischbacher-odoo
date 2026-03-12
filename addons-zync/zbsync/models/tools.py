# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import re
import random
import threading
from odoo.modules.registry import Registry
from odoo import api, models
import hashlib
import struct
from contextlib import contextmanager
from odoo.exceptions import ValidationError
from ..exceptions import RetryableJobError
import logging
from contextlib import closing

logger = logging.getLogger("zbs.tools")


def all_brackets_are_params_and_not_a_dict(code):
    pattern_brackets = r"\{[^{}]*\}"
    pattern_dicts = r"\{[^{}]*:[^{}]*\}"
    matches_brackets = re.findall(pattern_brackets, code)
    matches_dicts = re.findall(pattern_dicts, code)
    if not matches_dicts or len(matches_dicts) == len(matches_brackets):
        return False
    return True


def get_subclasses(env, parent_class_name, ignore=None):
    """
    Returns the inherited classes of a class
    """

    def _fetch(parent):
        for x in list(parent._inherit_children) + list(parent._inherits_children):
            yield x
            try:
                env[x]
            except KeyError:
                continue
            yield from _fetch(env[x])

    res = set()
    for x in _fetch(env[parent_class_name]):
        res.add(x)
    return res


class zbs_tools(models.AbstractModel):
    _name = "zbs.tools"
    _description = "Zync Tools"

    @api.model
    def zebrooset(self, data):
        from .zebrooset import ZebrooSet

        return ZebrooSet(data)

    @api.model
    def _get_subclasses(self, model):
        subclasses = get_subclasses(self.env, model)
        return subclasses

    @api.model
    def pg_hash(self, S):
        hasher = hashlib.sha1(str(S).encode())
        int_lock = struct.unpack("q", hasher.digest()[:8])
        return int_lock

    @api.model
    def pg_unlock(self, locks):
        if not isinstance(locks, (tuple, list)):
            locks = [locks]
        for lock in locks:
            int_lock = self.pg_hash(lock)
            self.env.cr.execute("SELECT pg_advisory_unlock(%s);", (int_lock,))

    @api.model
    def pg_advisory_lock(
        self, lock, ignore_retry=True, cr=None, wait=False, hostwide=False
    ):
        int_lock = self.pg_hash(lock)
        cr = cr or self.env.cr
        func = "pg_try_advisory_xact_lock"
        if wait:
            func = "pg_advisory_xact_lock"
        if hostwide:
            func = func.replace("_xact", "")
        lock_safe = lock.replace("{", "").replace("}", "").replace("'", "")
        cr.execute(
            (f"SELECT '{lock_safe}' as context; " f"SELECT {func}(%s);"), (int_lock,)
        )
        if wait:
            return

        excparams = {
            "msg": f"Could not acquire advisory lock on {lock} [{int_lock}]",
            "seconds": self._get_seconds(),
            "ignore_retry": ignore_retry,
        }

        try:
            acquired = cr.fetchone()[0]
            if not acquired:
                raise RetryableJobError(**excparams)
        except Exception as ex:
            raise RetryableJobError(**excparams) from ex
        return acquired

    @api.model
    @contextmanager
    def cursor_read_committed(self):
        with self.env["zbs.tools"].new_env(enabled=True) as env:
            self.cursor_change_to_read_committed(env.cr)
            yield env.cr
            self.commit()

    @api.model
    def pg_is_advisory_set(self, key):
        i = self.pg_hash(key)
        self.env.cr.execute(
            "select from pg_locks where locktype = 'advisory' and objid = %s;", (i,)
        )
        return bool(self.env.cr.fetchone())

    def cursor_change_to_read_committed(self, cr=None):
        if self._is_testing():
            return
        cr = cr or self.env.cr
        level = self.pg_transaction_level(cr)
        if level != "read committed":
            cr.commit()
            cr.execute("SET TRANSACTION ISOLATION LEVEL read committed;")

    def pg_transaction_level(self, cr=None):
        cr = cr or self.env.cr
        cr.execute("SHOW transaction_isolation;")
        level = cr.fetchone()[0]
        return level

    def pg_assert_read_committed(self, cr=None):
        if self._is_testing():
            return
        level = self.pg_transaction_level(cr)
        if level != "read committed":
            raise ValidationError(
                f"Transaction isolation level is not read committed: {level}"
            )

    @api.model
    @contextmanager
    def pglock(self, name, wait=None):
        hashes = []
        with self.new_env(enabled=True) as e2:
            if not isinstance(name, (tuple, list)):
                name = [name]
            for item in name:
                hash = self.pg_hash(item)
                e2["zbs.tools"].pg_advisory_lock(item, hostwide=False, wait=wait)
                hashes.append(hash)

            try:
                yield
            finally:
                e2["zbs.tools"].commit()
                e2["zbs.tools"].pg_unlock(name)

    @api.model
    def pg_advisory_lock_keyvalues(self, extra_string, key_values, ignore_retry=True):
        vals = []
        for key in sorted(key_values):
            vals.append((key, key_values[key]))
        vals = (extra_string or "") + str(vals)
        res = self.pg_advisory_lock(vals, ignore_retry=ignore_retry)
        logger.error(
            f"Advisory lock key: {vals} batchid: {self.env.context['zbs_batch_id']}"
        )
        return res

    @api.model
    def remove_python_comments(self, code):
        code = [
            x
            for x in code.strip().splitlines()
            if not x.strip().startswith("#") and x.strip()
        ]
        return "\n".join(code)

    @api.model
    def _exec_get_result(self, code, globals_dict):
        if not code:
            raise ValidationError("Code missing")

        code = self.remove_python_comments(code)

        dict2 = {k: v for (k, v) in globals_dict.items()}
        del globals_dict

        if self.env.context.get("zbs_instance"):
            dict2 = (
                self.env.context.get("zbs_instance")
                .with_context(self.env.context)
                ._get_default_objects(dict2)
            )
        else:
            dict2["env"] = self.env

        code = (code or "").strip()
        code = code.splitlines()
        is_oneliner = len(code) == 1 and not code[0].startswith("return ")
        if is_oneliner:
            if not code[0].startswith('"') and not code[0].startswith("'"):
                if all_brackets_are_params_and_not_a_dict(code[0]):
                    code[0] = 'f"' + code[0] + '"'
        if code and code[-1].startswith(" ") or code[-1].startswith("\t"):
            code.append("True")
        code[-1] = (
            "return " + code[-1] if not code[-1].startswith("return ") else code[-1]
        )
        code = "\n".join(["  " + x for x in code])
        keys = ",".join(list(dict2.keys()))
        wrapper = (
            f"def __wrap({keys}):\n"
            f"{code}\n\n"
            f"result_dict['result'] = __wrap({keys})"
        )
        result_dict = {}
        dict2["result_dict"] = result_dict
        exec(wrapper, dict2)
        return result_dict.get("result")

    @api.model
    def _is_testing(self):
        thread = threading.current_thread()
        return getattr(thread, "testing", False)

    @api.model
    @contextmanager
    def new_env(self, on_after_commit=None, enabled=False):
        su = self.env.su
        if not enabled:
            yield self.env
            self.env["zbs.tools"].flush()
            if not self._is_testing():
                self.commit()
            if on_after_commit:
                on_after_commit()

        elif self._is_testing():
            yield self.env
            if on_after_commit:
                on_after_commit()
        else:
            db_registry = Registry(self.env.cr.dbname)
            # with api.Environment.manage():
            with closing(db_registry.cursor()) as cr:
                env = api.Environment(cr, self.env.user.id, self.env.context, su)
                yield env
                env["zbs.tools"].flush()
                env["zbs.tools"].commit()
                if on_after_commit:
                    on_after_commit()

    @api.model
    def with_delay(self, instance, enabled=True, *args, **kwargs):
        return instance

    def flush(self, rec=None):
        if rec:
            if hasattr(rec, "flush_recordset"):
                # V16
                rec.flush_recordset()
            else:
                rec.flush()
        else:
            if hasattr(self.env, "flush_all"):
                self.env.flush_all()
            else:
                if hasattr(self.env["base"], "flush"):
                    self.env["base"].flush()

    @api.model
    def _get_seconds(self):
        return random.randint(1, 40)

    @api.model
    def rollback(self):
        before = self.pg_transaction_level()
        if not self._is_testing():
            self.env.cr.rollback()
            if before == "read committed":
                self.env.cr.execute("SET TRANSACTION ISOLATION LEVEL read committed;")
        level = self.pg_transaction_level()
        assert level == before

    @api.model
    def commit(self):
        before = self.pg_transaction_level()
        if not self._is_testing():
            self.env.cr.commit()
            if before == "read committed":
                self.env.cr.execute("SET TRANSACTION ISOLATION LEVEL read committed;")
        level = self.pg_transaction_level()
        assert level == before

    @api.model
    def expect_one(self, values):
        if len(values) > 1:
            raise ValueError(f"Expected one value: {values}")
        if len(values) == 0:
            raise ValueError(f"Expected at least one value: {values}")
        return values

    @api.model
    def _contains_dict_or_set(self, text):
        def find_matching_braces(text):
            stack = []
            matches = []

            for i, char in enumerate(text):
                if char == "{":
                    stack.append(i)
                elif char == "}":
                    if stack:
                        start = stack.pop()
                        matches.append((start, i))

            return matches

        matches_no_sets_no_dicts = re.findall(r"\{([^:{},]+)\}", text)
        matches_all_brackets = find_matching_braces(text)
        if len(matches_no_sets_no_dicts) == len(matches_all_brackets):
            return False
        return True

    @api.model
    def _eval_oneliner_or_code(self, lines, objects, expects_string_if_oneline=False):
        # find not dicts or sets
        orig_lines = lines
        lines = lines.strip()
        if len(lines.splitlines()) <= 1:
            has_dict_or_set = self._contains_dict_or_set(lines)
            if not has_dict_or_set and "{" in lines:
                lines = 'f"' + lines + '"'
            elif expects_string_if_oneline:
                lines = "'" + lines + "'"
        try:
            res = self.env["zbs.tools"]._exec_get_result(lines, objects)
        except:
            res = self.env["zbs.tools"]._exec_get_result(orig_lines, objects)
        return res

    @api.model
    def _as_python_object(self, data):
        from .zebrooset import ZebrooSet, _WrappedDict, _WrappedList

        if (
            isinstance(data, ZebrooSet)
            or isinstance(data, _WrappedList)
            or isinstance(data, _WrappedDict)
        ):
            return data._as_python_object()
        if isinstance(data, (dict, list)):
            return data
        elif isinstance(data, str):
            return ZebrooSet._loads(data, env=self.env)._as_python_object()

        else:
            raise NotImplementedError(f"Not supported type: {type(data)}")

    @api.model
    def do_flush(self, obj):
        # Untested
        if hasattr(obj, "flush_model"):
            obj.flush_recordset()
        else:
            obj.flush()

    @api.model
    def do_clear_cache(self, obj=None, function_name=None):
        # auch gefunden:         self.pool.clear_all_caches()
        # https://github.com/odoo/odoo/pull/87527
        # # process pending computations and updates
        # records.env.flush_all()                 # all fields of all models
        # records.flush_model(fnames)             # the fields of all records of the model
        # records.flush_recordset(fnames)         # the fields of the given records

        # # invalidate the cache of fields
        # records.env.invalidate_all()            # all fields of all models
        # records.invalidate_model(fnames)        # the fields of all records of the model
        # records.invalidate_recordset(fnames)    # the fields of the given records
        # self.env['zbs.mapping']._apply_lookup_search.clear_cache(self.env['zbs.mapping'])
        # 16.0 getattr(obj , function_name).clear_cache(obj)
        if function_name or obj or isinstance(obj, models.BaseModel):
            if function_name:
                assert isinstance(function_name, str), (
                    "Function name must be string not %s" % function_name
                )
                if function_name:
                    funcobj = getattr(obj, function_name)
            assert obj or isinstance(
                obj, models.BaseModel
            ), "Object must be defined, if function name is defined"

            if function_name and hasattr(funcobj, "clear_cache"):
                # V16
                funcobj.clear_cache(obj)
            else:
                # V17 and above?
                if not obj:
                    obj.invalidate_model(flush=True)
                else:
                    obj.invalidate_recordset(flush=True)
        else:
            # Approved V16
            if obj:
                obj.clear_caches()
            else:
                self.env.registry.clear_cache()

