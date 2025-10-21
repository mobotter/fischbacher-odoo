# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import http.cookiejar
from odoo import _, api, fields, models, SUPERUSER_ID, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from datetime import date, datetime
from odoo.addons.zbsync.exceptions import ConfigurationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from copy import deepcopy
from contextlib import contextmanager
import urllib.request
import logging
from copy import deepcopy

logger = logging.getLogger("zbsync.odoo_connection")


class WriteValues(dict):
    def __init__(self, *params, **kwparams):
        super().__init__(*params, **kwparams)
        self.odoo_id = None
        self.filter_delta = False
        self.default_values = []

    def set_odooid(self, id):
        self.odoo_id = id


class RemoveMe(object):
    def __init__(self, id):
        self.id = id


class OdooConnection(models.Model):
    _inherit = [
        "zbs.connection",
        "zbs.connection.mixin.usernamepassword",
        "zbs.connection.mixin.hostport",
    ]
    _name = "zbs.connection.odoo"
    _description = "Zync Odoo Connection"

    timeout = fields.Integer("Timeout", default=120)

    port = fields.Integer(default=8069)
    dbname = fields.Char("DBName")
    is_local_connection = fields.Boolean(compute="_compute_is_local_connection")
    ssl = fields.Boolean("SSL")
    version = fields.Selection([(str(float(i)), str(float(i))) for i in range(99)])
    basic_auth_username = fields.Char("Basic Auth Username")
    basic_auth_password = fields.Char("Basic Auth Password")
    proxy_ids = fields.Many2many("zbs.web.proxy", string="Proxies")
    lang_id = fields.Many2one("res.lang", string="Language")
    lang = fields.Char(related="lang_id.code")
    context = fields.Text(
        "Odoo Context", help="e.g. {'no_reset_password': True}", default="{}"
    )

    def _set_company_context(self, obj):
        if "zbs_environment" in self.env.context:
            company = self.env["zbs.environment"]._extract_company(
                self.env.context["zbs_environment"]
            )
            if company:
                return obj.with_company(company)
        return obj

    def _get_context(self, context_string, objects):
        def _eval(context):
            context = context or "{}"
            if context.startswith("{"):
                context = f"res = {context}\nres"
            context = self.env["zbs.tools"]._exec_get_result(
                context,
                objects,
            )
            return context

        context = _eval(self.context)
        context.update(_eval(context_string))
        context.setdefault("active_test", False)
        context.setdefault("lang", self.lang)
        return context

    def _compute_is_local_connection(self):
        for rec in self:
            rec.is_local_connection = rec == self.env.ref(
                "zbsync_odoo.localodoo_connection"
            )

    @tools.ormcache("self.id", "model", "fieldname")
    def _get_field(self, model, fieldname):
        assert isinstance(model, str)
        res = self._get_fields_of_obj(model)
        return res[fieldname]

    @tools.ormcache("self.id", "model")
    def _get_obj(self, model):
        assert isinstance(model, str)
        if self.is_local_connection:
            obj = self.env[model]
            for k, v in self.env.context.get("ODOORPC_CONTEXT", {}).items():
                obj = obj.with_context(**{k: v})
            return obj
        else:
            rpc = self._get_odoo()
            for k, v in self.env.context.get("ODOORPC_CONTEXT", {}).items():
                rpc.env.context[k] = v
            res = rpc.env[model]
            setattr(res, "_zbsync_odoo_connection", self.id)
            return res

    def _test_python_import(self):
        from .. import odoorpc

    @tools.ormcache("self.id")
    def _get_odoo(self):
        protocol, http_protocol = None, None
        if self.ssl:
            protocol = "jsonrpc+ssl"
            http_protocol = "https"
        else:
            protocol = "jsonrpc"
            http_protocol = "http"
        opener_params = []
        if self.basic_auth_username:
            pwd_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            pwd_mgr.add_password(
                None,
                f"{http_protocol}://{self.host}",
                self.basic_auth_username,
                self.basic_auth_password,
            )
            auth_handler = urllib.request.HTTPBasicAuthHandler(pwd_mgr)
            opener_params.append(auth_handler)

        if self.proxy_ids:
            proxies = self.proxy_ids._get_for_requests()
            proxy = urllib.request.ProxyHandler(proxies)
            opener_params.append(proxy)
        cookie_jar = http.cookiejar.CookieJar()
        opener_params.insert(0, urllib.request.HTTPCookieProcessor(cookie_jar))
        opener = urllib.request.build_opener(*opener_params)
        dbname = self.dbname
        if not dbname:
            raise ConfigurationError("Please configure database name on connection.")

        from .. import odoorpc

        odoo = odoorpc.ODOO(
            self.host,
            port=self.port,
            protocol=protocol,
            version=self.version or None,
            timeout=self.timeout,
            opener=opener,
        )
        odoo.json(
            "/web/session/authenticate",
            {
                "db": dbname,
                "login": self.username,
                "password": self.password,
            },
        )

        # be compatible with more than 1 database
        odoo.login(dbname, self.username, self.password)
        return odoo

    @tools.ormcache("self.id", "model")
    def _get_fields_of_obj(self, model):
        obj = self._get_obj(model)
        _fields = self._odoo_search(
            obj.env["ir.model.fields"], [("model_id.model", "=", model)]
        )
        res = [
            {
                "comodel_name": x.relation,
                "name": x.name,
                "type": x.ttype,
                "inverse_name": x.relation_field,
            }
            for x in _fields
        ]
        d = {}
        for rec in res:
            d[rec["name"]] = rec
        return d

    def _odoo_search(self, obj, domain, *params, **kwparams):
        domain = self._fix_dates_in_domain(domain)
        return_ids = kwparams.pop("return_ids", False)
        if self.is_local_connection:
            found = obj.search(domain, *params, **kwparams)
            if return_ids:
                return found.ids
            return found
        else:
            ids = obj.search(domain, *params, **kwparams)
            if return_ids:
                return ids
            records = obj.browse(ids)
            return records

    @contextmanager
    def _filter_out(self, vals):
        store = {}
        for f in ["___kept_input"]:
            if f in vals:
                store[f] = vals.pop(f)
        try:
            yield vals
        finally:
            for k, v in store.items():
                vals[k] = v

    def _extract_dotted_field_values(self, vals):
        data = {}
        for fieldname in list(vals.keys()):
            if "." in fieldname:
                data[fieldname] = vals.pop(fieldname)
        return data

    def _apply_dotted_fieldvalue(self, record, values):
        for k, v in values.items():
            while "." in k:
                key1, k = k.split(".", 1)
                record = record[key1]
            try:
                record.write({k: v})
            except:
                raise

    def _odoo_create(self, instance, obj, vals_list):
        if self.env.context.get("zbs_lock_resources"):
            return None
        pipeline = self.env.context["zbs_pipeline"]
        pipeline.log(f"Odoo Dumper: creating {len(vals_list)} x {obj._name}")

        arr_dotted_vals, arr_vals2 = [], []
        for val in vals_list:
            logger.debug(f"Odoo Connection Creating Record: {val}")
            dotted_vals = self._extract_dotted_field_values(val)
            arr_dotted_vals.append(dotted_vals)
            with self._filter_out(val) as val2:
                arr_vals2.append(deepcopy(val2))

        created_objects = obj.create(arr_vals2)
        for i, objinstance in enumerate(created_objects):
            if self.is_local_connection:
                id = objinstance.id
            else:
                id = objinstance

            val = vals_list[i]
            val["id"] = id
            del i
            del id

        for i, val in enumerate(vals_list):
            id = val["id"]
            self._handle_create_write(obj, id, val)
            dotted_vals = arr_dotted_vals[i]
            if dotted_vals:
                id = val["id"]
                record = obj.browse(id)
                self._apply_dotted_fieldvalue(record, dotted_vals)
        return vals_list

    def _odoo_write(self, instance, obj, vals):
        if self.env.context.get("zbs_lock_resources"):
            return None
        pipeline = self.env.context["zbs_pipeline"]
        pipeline.log(f"Updating {obj._name}:\n{vals}")
        ids = []
        dotted_vals = []
        for val in vals:
            assert isinstance(val, (WriteValues, RemoveMe))
            if isinstance(val, RemoveMe):
                continue
            record = obj.browse(val.odoo_id)
            if val.default_values:
                self._filter_default_values(val.default_values, record, val)
            if val.filter_delta or (self.env.context.get("zbs_dumper_only_new_values")):
                val = self._filter_delta_values(record, val)

            if val and not (val and len(val.keys()) == 1 and "id" in val):
                with self._filter_out(val) as val2:
                    dotted_vals.append(self._extract_dotted_field_values(val2))
                    if val2:
                        record.write(val2)
                if dotted_vals:
                    self._apply_dotted_fieldvalue(record, dotted_vals[0])
            ids.append((val.odoo_id, val))
            self._handle_create_write(record, val.odoo_id, val)
        return ids

    def _handle_create_write(self, model, odoo_id, vals):
        for field in ["create_date", "write_date"]:
            if isinstance(vals, dict):
                vals = [vals]
            for val in vals:
                if val.get(field):
                    if not self.is_local_connection:
                        raise ValidationError(
                            "Cannot update create_date / write_date remotely"
                        )
                    table = model._table
                    self.env.cr.execute(
                        f"update {table} set {field}=%s where id=%s",
                        (val[field], odoo_id),
                    )

    def _odoo_unlink(self, instance, obj, ids):
        if self.env.context.get("zbs_lock_resources"):
            return None
        pipeline = self.env.context["zbs_pipeline"]
        pipeline.log(f"Deleting {obj._name}:\n{ids}")
        obj.browse(ids).unlink()
        return ids

    def _filter_default_values(self, fields, inst, data):
        for field in fields:
            if inst[field]:
                if field in data:
                    data.pop(field)

    def _filter_delta_values(self, inst, data):
        def _turn_into_datestring(v, format, maxlen):
            if not v:
                return v
            if isinstance(v, (date, datetime)):
                return v.strftime(format)
            result = v[:maxlen]
            if len(result) < maxlen:
                result += " 00:00:00"

        if not inst:
            return data
        all_fields = self._get_fields_of_obj(inst._name)
        for k in list(data.keys()):
            if "." in k:
                continue
            if k in ["___kept_input"]:
                continue
            f = all_fields[k]
            if not f:
                raise KeyError(k)

            if f["type"] in ["integer", "float", "char", "text", "binary", "boolean"]:
                if f["type"] == "integer" and isinstance(data[k], str):
                    if data[k]:
                        data[k] = int(data[k])
                    else:
                        data[k] = 0
                elif f["type"] == "float" and isinstance(data[k], str):
                    if data[k]:
                        data[k] = float(data[k])
                    else:
                        data[k] = 0
                elif f["type"] == "char" and isinstance(data[k], (int, float)):
                    data[k] = str(data[k])
                elif f["type"] == "boolean" and isinstance(data[k], str):
                    if data[k] in ["1", "true", "True", "TRUE"]:
                        data[k] = True
                    elif data[k] in ["0", "false", "False", "FALSE"]:
                        data[k] = False
                    else:
                        raise NotImplementedError(data[k])
                v1 = data[k]
                v2 = inst[k]
                if v1 == v2:
                    del data[k]
            elif f["type"] in ["date"]:
                v1 = _turn_into_datestring(
                    (data[k] or "") or False, DEFAULT_SERVER_DATE_FORMAT, 10
                )
                v2 = _turn_into_datestring(
                    (inst[k] or "") or False, DEFAULT_SERVER_DATE_FORMAT, 10
                )
                if v1 == v2:
                    del data[k]
            elif f["type"] in ["datetime"]:
                v1 = _turn_into_datestring(
                    (data[k] or "") or False, DEFAULT_SERVER_DATETIME_FORMAT, 19
                )
                v2 = _turn_into_datestring(
                    (inst[k] or "") or False, DEFAULT_SERVER_DATETIME_FORMAT, 19
                )
                if v1 == v2:
                    del data[k]
            elif f["type"] == "many2one":
                v1 = data[k]
                v2 = inst[k].id
                if v1 == v2:
                    del data[k]
            elif f["type"] in ["one2many", "many2many"]:
                new_array = []
                if data[f["name"]]:
                    for x in data[f["name"]]:
                        if x and x[0] == 1:
                            inst_value = inst[f["name"]]
                            sub_inst = list([x1 for x1 in inst_value if x1.id == x[1]])
                            # not odoorpc compatible / error raised
                            # sub_inst = list(inst_value.filtered(lambda x1: x1.id == x[1]))
                            if sub_inst:
                                sub_inst = sub_inst[0].browse([x.id for x in sub_inst])
                                if tupled := isinstance(x, tuple):
                                    tupled = True
                                    x = list(x)
                                x[2] = self._filter_delta_values(sub_inst, x[2])
                                if tupled:
                                    x = tuple(x)
                                if not x[2]:
                                    continue
                        new_array.append(x)
                if not new_array:
                    data.pop(f["name"])
                else:
                    data[f["name"]] = new_array
        return data

    def write(self, vals):
        res = super().write(vals)
        self.env['zbs.tools'].do_clear_cache()
        return res

    def _fix_dates_in_domain(self, domain):
        """
        json rpc cannot handle datetime
        """
        d2 = []
        for x in domain or []:
            if isinstance(x, str):
                d2.append(x)
            elif isinstance(x, (tuple, list)):
                x = list(x)
                if len(x) == 3 and isinstance(x[2], date):
                    x[2] = x[2].strftime(DEFAULT_SERVER_DATE_FORMAT)
                elif len(x) == 3 and isinstance(x[2], datetime):
                    x[2] = x[2].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                x = tuple(x)
                d2.append(x)
        return d2
