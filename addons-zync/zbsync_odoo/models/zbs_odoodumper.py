# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
"""
Expects key columns in [{'___keys': ....}]
"""
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.addons.zbsync.models.zebrooset import ZebrooSet
from .zbs_odooconnection import WriteValues, RemoveMe
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import date, datetime
from contextlib import contextmanager
import time
import logging

logger = logging.getLogger("zbsync.odoo_dumper")

# TODO cache fields
# TODO locking if main key exists or so
# TODO raise retryable job error then
# TODO domain mapping values
"""

{
    "name": "name1",
    "___keys": ["name"],
    "___keys_multi_ok": True/False,
    "___keys_delete": ["line_ids"], list of fields, where to delete missing keys
    "___filter_to_delta": True/False
    "___default_values: ['field1', 'field2']
    "line_ids": [
        {.....},
        {.....},
        {.....},
    ],
}


"""

ALL_META_ATTRS = [
    "___keys",
    "___keys_multi_ok",
    "___keys_delete",
    "___filter_to_delta",
    "___default_values",
    "___kept_input",
    "___no_update",
    "___no_insert",
]


def is_a_dict(v):
    if isinstance(v, dict):
        return True
    try:
        classname = v.__class__.__name__
    except:
        classname = ""
    return classname in ["ZebrooSet", "_WrappedDict"]


class OdooDumper(models.Model):
    _inherit = ["zbs.dumper", "zbs.dumper.mixin.cu", "zbs.odoo.mixin.connection"]
    _name = "zbs.dumper.odoo"
    _description = "Odoo Dumper"

    only_new_values = fields.Boolean("Only New Values", tracking=True)
    lang_id = fields.Many2one("res.lang", string="Language")
    lang = fields.Char(related="lang_id.code")
    company_id = fields.Many2one("res.company", string="Company")

    context = fields.Text(
        "Odoo Context", help="e.g. {'no_reset_password': True}", default="{}"
    )

    @api.constrains("context")
    def _strip(self):
        for rec in self:
            stripped = (rec.context or "").strip()
            if stripped != rec.context:
                rec.context = stripped

    def process(self, instance, data, errors=None):
        logger.debug(f"Odoo Dumper Processing {instance}")
        pipeline = self.env.context["zbs_pipeline"]
        self = self.with_context(instance=instance)
        if self.company_id:
            self = self.with_company(self.company_id)
        self.connection_id.clear_caches()
        content = data._d
        if isinstance(content, dict):
            content = [content]
        if not self.model:
            raise ValidationError("Please provide a model!")

        context = self.connection_id._get_context(
            self.context, dict(instance=instance, data=data)
        )
        context["lang"] = self.lang
        self = self.with_context(ODOORPC_CONTEXT=context)

        obj = self.connection_id._get_obj(self.model)
        obj = self.connection_id._set_company_context(obj)
        for k, v in context.items():
            obj = obj.with_context(k=v)
        zbs_dumper_only_new_values = self.only_new_values
        if self.env.context.get("zbs_lock_resources"):
            self._get_create_write_values(
                obj,
                content,
                root=True,
                input=data,
                dry_run_lock_resources=self.env.context.get("zbs_lock_resources"),
            )
            return []

        create_vals, write_vals = self.with_context(
            zbs_dumper_only_new_values=zbs_dumper_only_new_values
        )._get_create_write_values(
            obj,
            content,
            root=True,
            input=data,
            dry_run_lock_resources=False,
        )
        data = {"created": [], "updated": []}
        data["created"] += self.connection_id._odoo_create(
            instance,
            obj,
            create_vals,
        )
        pipeline.log(f"Creating for {obj._name}:\n{create_vals}")
        data["updated"] = self.connection_id.with_context(
            zbs_dumper_only_new_values=zbs_dumper_only_new_values
        )._odoo_write(
            instance,
            obj,
            write_vals,
        )

        data["upserted_ids"] = [x["id"] for x in data.get("created", [])] + [
            x[0] for x in data.get("updated", [])
        ]
        return instance.Result([data])

    def _get_create_write_values(
        self,
        obj,
        records,
        parent_id=None,
        inverse_field=None,
        delete_x2many=False,
        parent_field=None,
        parent_obj=None,
        root=False,
        input=None,
        keep_key_info_for_create=False,
        keep_key_info_for_write=False,
        dry_run_lock_resources=False,
    ):
        create_vals, write_vals = [], []
        add_domain = []
        ids = []
        for (
            record,
            id,
            kept_input,
        ) in self._iterate_for_values(
            records, obj, ids, inverse_field, parent_id, root, input
        ):
            logger.debug(f"Analyzing {record}")
            no_update = record.get("___no_update") if hasattr(record, "get") else False
            no_create = record.get("___no_create") if hasattr(record, "get") else False
            if not id and no_create:
                continue
            if id and no_update:
                continue
            (
                values,
                _filter_to_delta,
                _default_values,
            ) = self._transform_input_to_values(
                record,
                id,
                obj,
                parent_obj,
                keep_key_info_for_create=keep_key_info_for_create,
                keep_key_info_for_write=keep_key_info_for_write,
                dry_run_lock_resources=dry_run_lock_resources,
            )
            del record

            if root:
                values["___kept_input"] = kept_input
            if not id:
                create_vals.append(values)
            else:
                if not keep_key_info_for_write and "___keys" in values:
                    del values["___keys"]
                values = WriteValues(values)
                values.set_odooid(id)
                values.default_values = _default_values
                values.filter_delta = _filter_to_delta
                write_vals.append(values)

        if parent_id and delete_x2many and not dry_run_lock_resources:
            self._execute_kill_command_delete_x2many(
                obj,
                add_domain,
                ids,
                parent_field,
                parent_id,
                parent_obj,
                write_vals,
            )

        return create_vals, write_vals

    @api.model
    def _sort_fields(self, record, obj_fields, obj):
        def sortit(fieldname):
            if fieldname in ALL_META_ATTRS:
                return -1
            try:
                fieldpart = fieldname.split(".")[0]
                field = obj_fields[fieldpart]
            except KeyError:
                if fieldname.startswith("___"):
                    return -1
                raise KeyError(f"{fieldpart} not in {obj._name}")
            if not field:
                if fieldname.startswith("___"):
                    return 0
                raise KeyError(fieldname)
            # higher prio, so that "id" is evaluated first
            if field["type"] in ["one2many", "many2many"]:
                return 100
            if field["type"] in ["many2one"]:
                return 10
            return 0

        sorteddict = {}
        for fieldname in record:
            sorteddict[fieldname] = sortit(fieldname)
        for fieldname, value in sorted(record.items(), key=lambda x: sorteddict[x[0]]):
            yield fieldname, value

    @api.model
    def _get_obj_field(self, fieldname, obj, obj_fields, obj_fields_dict):
        field = None
        if fieldname not in ALL_META_ATTRS:
            if not fieldname.startswith("___") and fieldname not in [
                x["name"] for x in obj_fields
            ]:
                raise KeyError(f"{fieldname} not in {obj._name}")

            field = [x for x in obj_fields if x.name == fieldname]
            if field:
                field = field[0]
        return field

    def _slice_dictionary(
        self,
        record,
        id,
        obj,
        obj_fields_dict,
        values,
        parent_obj,
        _filter_to_delta,
        _default_values,
        keep_key_info_for_create=False,
        keep_key_info_for_write=False,
        dry_run_lock_resources=False,
    ):
        for fieldname, value in self._sort_fields(record, obj_fields_dict, obj):
            field = obj_fields_dict.get(fieldname)

            if field and field["type"] == "many2one":
                if fieldname in record:
                    if "." in fieldname:
                        values[fieldname] = record[fieldname]
                    else:
                        values[fieldname] = self._import_many2one(
                            obj,
                            fieldname,
                            record[fieldname],
                            dry_run_lock_resources=dry_run_lock_resources,
                        )
            elif field and field["type"] in ["one2many", "many2many"]:
                values[fieldname] = self._import_x2many(
                    obj,
                    fieldname,
                    record[fieldname],
                    parent_id=id or record.get("id"),
                    parent_obj=parent_obj,
                    inverse_field=field["inverse_name"],
                    delete_keys=fieldname in record.get("___keys_delete", []),
                    dry_run_lock_resources=dry_run_lock_resources,
                )

            elif fieldname == "___filter_to_delta":
                _filter_to_delta = True
            elif fieldname == "___default_values":
                _default_values = value

            elif (
                keep_key_info_for_create or keep_key_info_for_write
            ) and fieldname == "___keys":
                values[fieldname] = value

            elif fieldname in ALL_META_ATTRS:
                continue
            elif fieldname.startswith("___"):
                continue
            else:
                if isinstance(value, datetime):
                    value = value.strftime(DTF)
                if isinstance(value, date):
                    value = value.strftime(DT)
                values[fieldname] = value
        return _filter_to_delta, _default_values, values

    def _iterate_for_values(
        self, records, obj, ids, inverse_field, parent_id, root, input
    ):
        add_domain = []
        if inverse_field and parent_id:
            add_domain = [(inverse_field, "=", parent_id)]
        for index, record in enumerate(records):
            kept_input = None
            if isinstance(record, (dict, list)):
                record = self.env["zebrooset"].rs(record)
            if root:
                kept_input = self._keep_input(
                    index,
                    record,
                    (
                        self.env["zebrooset"].rs(input)
                        if isinstance(input, (dict, list))
                        else input
                    ),
                )
            if inverse_field and not parent_id:  # one2many:
                id = None
            else:
                id = self._find_id(
                    obj,
                    record,
                    add_domain=add_domain,
                )
            ids.append(id)

            if root:
                if not id and not self.do_insert:
                    continue
                if id and not self.do_update:
                    continue

            yield record, id, kept_input

    def _transform_input_to_values(
        self,
        record,
        id,
        obj,
        parent_obj,
        keep_key_info_for_create=False,
        keep_key_info_for_write=False,
        dry_run_lock_resources=False,
    ):
        _filter_to_delta = False
        _default_values = []
        values = {}
        obj_fields_dict = self.connection_id._get_fields_of_obj(obj._name)
        if isinstance(record, (str, float, datetime, date)):
            if id:
                record = {"id": id}
            elif self.connection_id.is_local_connection:
                record = {obj._rec_name: record}
            else:
                # TODO fits in 99,9% of cases, but not always; how to retrieve the rec_name
                record = {"name": record}

        if isinstance(record, int):
            record = {"id": record}
        if isinstance(record, models.Model):
            if self.connection_id.is_local_connection:
                record = record
            else:
                # TODO unclear - not understood the following block anymore
                if record.ids:
                    record = record
                else:
                    raise ValidationError(
                        f"Cannot dump to remote odoo system some odoo instances like {record}.\n"
                        "There are no key informations given. Please map those records to "
                        "[]/{} combination(s) and set appropriate keys.\n\n"
                        "A thorough explanation can be found here: TODO"
                    )
        if type(record).__name__ == "_WrappedList" or isinstance(record, list):
            if type(record).__name__ == "_WrappedList":
                record = record._l
            values = record
        elif isinstance(record, models.Model):
            if self.connection_id.is_local_connection:
                values = [6, 0, record.ids]
            else:
                # TODO unclear - not understood the following block anymore like above
                if record.ids:
                    values = [6, 0, record.ids]
                else:
                    raise ValidationError(
                        f"Cannot dump to remote odoo system some odoo instances like {record}.\n"
                        "There are no key informations given. Please map those records to "
                        "[]/{} combination(s) and set appropriate keys.\n\n"
                        "A thorough explanation can be found here: TODO"
                    )
        else:
            _filter_to_delta, _default_values, values = self._slice_dictionary(
                record,
                id,
                obj,
                obj_fields_dict,
                values,
                parent_obj,
                _filter_to_delta,
                _default_values,
                keep_key_info_for_create=keep_key_info_for_create,
                keep_key_info_for_write=keep_key_info_for_write,
                dry_run_lock_resources=dry_run_lock_resources,
            )
        return values, _filter_to_delta, _default_values

    def _execute_kill_command_delete_x2many(
        self, obj, add_domain, ids, parent_field, parent_id, parent_obj, write_vals
    ):
        kill_command = self._delete_x2many_comparing_keys(
            obj,
            add_domain,
            list(filter(bool, ids)),
            parent_field=parent_field,
            parent_id=parent_id,
            parent_obj=parent_obj,
        )
        for kill in kill_command:
            kill.parent_id = parent_id
            kill.parent_field_name = parent_field["name"]
            kill.parent_obj = parent_obj._name
            write_vals.append(kill)

    def _delete_x2many_comparing_keys(
        self,
        obj,
        add_domain,
        keep_ids,
        parent_field,
        parent_id=None,
        parent_obj=None,
    ):
        ttype = parent_field["type"]
        if ttype == "one2many":
            existing = self.connection_id._odoo_search(obj, add_domain)
            kill = [
                x.id for x in existing if x.id not in keep_ids
            ]  # compatible with remote odoorpc
            self.connection_id._odoo_unlink(self.env.context["instance"], obj, kill)
            return []
        elif ttype == "many2many":
            if parent_id:
                parent_field_name = parent_field["name"]
                existing = parent_obj.browse(parent_id)[parent_field_name]
                return [
                    RemoveMe(x.id) for x in existing if x.id not in keep_ids
                ]  # compatible with remote odoorpc
            else:
                return []
        else:
            raise NotImplementedError()

    def _import_many2one_keyvalues(self, obj, values):
        key_values, domain = self._xtract_keyvalues(values)
        if not key_values:
            if isinstance(values, str):
                if self.connection_id.is_local_connection:
                    namefield = obj._rec_name
                else:
                    try:
                        # not possible to read out obj._rec_name on remote side
                        self.connection_id._get_field(obj._name, "name")
                        namefield = "name"
                    except KeyError:
                        raise Exception(
                            f"There is no name field on the object '{obj._name}'. Try to explicitly set the name field."
                        )
                key_values = {namefield: values}
        return key_values

    def _import_many2one(self, obj, fieldname, values, dry_run_lock_resources=False):
        if not values:
            return False

        comodel_name = self.connection_id._get_field(
            obj._name, fieldname.split(".")[0]
        )["comodel_name"]
        if isinstance(values, int):
            return values
        elif isinstance(values, bool) and not values:
            return False

        key_values = self._import_many2one_keyvalues(obj, values)

        obj = self.connection_id._get_obj(comodel_name)
        create_vals, write_vals = self._get_create_write_values(
            obj, [values], dry_run_lock_resources=dry_run_lock_resources
        )

        assert len(create_vals) + len(write_vals) <= 1

        if create_vals:
            if dry_run_lock_resources:
                if key_values:
                    dry_run_lock_resources(f"{obj._name}:{key_values}")
                return False
            else:
                ids = self.connection_id._odoo_create(
                    self.env.context["instance"],
                    obj,
                    create_vals,
                )
                return ids[0]["id"]
        elif write_vals:
            # remove key values
            # otherwise updated without any need and write_date should not be updated
            if key_values:
                for key in key_values:
                    for item in write_vals:
                        if hasattr(item, "pop") and key in item:
                            item.pop(key)
            ids = self.connection_id._odoo_write(
                self.env.context["instance"],
                obj,
                write_vals,
            )
            if ids is not None:  # logck resources
                return ids[0][1].odoo_id
        else:
            return False

    def _import_x2many(
        self,
        obj,
        fieldname,
        values,
        parent_id=None,
        parent_obj=None,
        inverse_field=None,
        delete_keys=None,
        dry_run_lock_resources=False,
    ):
        if not values:
            return None
        field = self.connection_id._get_field(obj._name, fieldname)
        comodel_name = field["comodel_name"]
        parent_obj = obj
        obj = self.connection_id._get_obj(comodel_name)
        create_vals, write_vals = self._get_create_write_values(
            obj,
            values,
            parent_id=parent_id,
            inverse_field=inverse_field,
            delete_x2many=delete_keys,
            parent_field=field,
            parent_obj=parent_obj,
            keep_key_info_for_create=True,
            keep_key_info_for_write=True,
            dry_run_lock_resources=dry_run_lock_resources,
        )
        res = []

        def _remove_keys_from_values(values):
            if (
                isinstance(values, dict) or type(values).__name__ == "_WrappedDict"
            ) and "___keys" in values:
                values.pop("___keys")

        def _remove_keyvalues_from_values(values):
            if (
                isinstance(values, dict) or type(values).__name__ == "_WrappedDict"
            ) and "___keys" in values:
                for keyfield in values["___keys"]:
                    if keyfield in values:
                        values.pop(keyfield)

        for w in write_vals:
            if dry_run_lock_resources and w:
                key_values, domain = self._xtract_keyvalues(w)
                _remove_keyvalues_from_values(w)
                _remove_keys_from_values(w)
                if w:
                    logger.error(w)

                    dry_run_lock_resources(f"{obj._name}:{key_values}")
                continue

            _remove_keyvalues_from_values(w)
            _remove_keys_from_values(w)
            if inverse_field:
                if w:
                    res.append((1, w.odoo_id, w))
                else:
                    res.append((4, w.odoo_id))
            else:
                if w and not isinstance(w, RemoveMe) and not dry_run_lock_resources:
                    self.connection_id._odoo_write(
                        self.env.context["instance"],
                        obj,
                        [w],
                    )
                if isinstance(w, RemoveMe):
                    res.append((3, w.id))
                else:
                    res.append((4, w.odoo_id))

        for c in create_vals:
            if dry_run_lock_resources:
                key_values, domain = self._xtract_keyvalues(c)
                dry_run_lock_resources(f"{obj._name}:{key_values}")
            _remove_keys_from_values(c)
            if type(c).__name__ == "_WrappedList" or isinstance(c, list):
                if type(c).__name__ == "_WrappedList":
                    c = c._l
                res += [c]
            elif isinstance(c, models.Model):
                res += [[4, x.id] for x in c]
            else:
                res.append((0, 0, c))

        return res

    def _xtract_keyvalues(self, values, ignore_case=False):
        if "___keys" not in values:
            return None, None
        keys = values["___keys"]
        keyvalues = {}
        domain = []
        for key in keys:
            operator = "="
            if ignore_case and isinstance(values[key], str):
                operator = "=ilike"

            if is_a_dict(values[key]):
                # TODO: make test - used at gremienart child_ids and parent_ids
                # example: child_id = {'name': 'product1', '__keys': ['name']}
                subkeyvalues, subdomain = self._xtract_keyvalues(
                    values[key], ignore_case=ignore_case
                )
                if subdomain:
                    for dom in subdomain:
                        dom[0] = key + "." + dom[0]
                    domain += subdomain
                if subkeyvalues:
                    keyvalues[key] = subkeyvalues
            else:
                domain_value = values[key]
                if operator in ["in", "not in"] and not isinstance(
                    domain_value, (list, tuple)
                ):
                    domain_value = [domain_value]
                domain.append([key, operator, domain_value])
                keyvalues[key] = values[key]
        return keyvalues, domain

    def _find_id(self, obj, values, add_domain=[]):
        if isinstance(values, int):
            return values
        if isinstance(values, str):
            res = obj.name_search(values, operator="=")
            if res:
                return res[0][0]
            return None

        if not isinstance(values, dict) and values.__class__.__name__ not in [
            "ZebrooSet",
            "_WrappedDict",
        ]:
            return None
        if "id" in values and values["id"]:
            return values["id"]

        if "___keys" in values:
            order = "id desc"

            def _get_domain(ignore_case):
                keyvalues, domain = self._xtract_keyvalues(
                    values, ignore_case=ignore_case
                )

                if add_domain:
                    domain = expression.AND([domain, add_domain])
                return keyvalues, domain

            # Just looking for key values shall not lock them; just creating them
            records = self.connection_id._odoo_search(
                obj, _get_domain(False)[1], order=order
            )

            if not len(records):
                records = self.connection_id._odoo_search(
                    obj, _get_domain(True)[1], order=order
                )

            if len(records) > 1:
                if values.get("___keys_multi_ok"):
                    records = records[0]
                else:
                    domain = _get_domain(False)[1]
                    raise ZebrooSet.TooManyrecordsException(
                        f"Too many records found for: {domain} - "
                        "you can set keys multi ok to change this behaviour."
                    )
            if not records:
                return None
            return records[0].id

    def _compute_capas(self):
        for rec in self:
            rec.can_keys = True
            rec.can_keys_multi_ok = True
            rec.can_delete_one2many = True
            rec.can_compare_delta = True

    def can_lock_resources(self):
        return True
