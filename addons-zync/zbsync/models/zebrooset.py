# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import models
from odoo.api import Environment
import dateutil
import base64
import lxml
from datetime import datetime, date, time
from decimal import Decimal
import json
import uuid
from pathlib import Path
from odoo import api, models
import logging

logger = logging.getLogger("zebrooset")


class NoArg(object):
    pass


def _is_scalar(value):
    value = get_python_type(value)
    if isinstance(value, (list, tuple, dict)):
        return False
    return True


def _dumps(self, content=NoArg, env=None):
    # be flexible when calling ZebrooSet._dumps(a, self.env)
    if isinstance(content, Environment):
        content, env = self, content
    if content == NoArg:
        content = self._as_python_object()
    if env:
        content = env["zebrooset"]._prepare_dump(content)
    return json.dumps(content, cls=Encoder, env=env, indent=4)


def walk_the_line(d):
    while True:

        def make_list(x):
            if isinstance(x, list):
                return x
            if isinstance(x, _WrappedList):
                return x._l
            if isinstance(x, dict):
                return x
            if isinstance(x, ZebrooSet) and isinstance(x._d, list):
                return x._d
            return None

        l = make_list(d)
        if isinstance(l, dict):
            d = l
            break
        elif l and len(l) == 1:
            d = l[0]
        else:
            break
    return d


def get_python_type(data):
    if isinstance(data, (ZebrooSet, _WrappedDict, _WrappedList)):
        return data._as_python_object()
    if isinstance(data, (dict, list, tuple)):
        return data
    return data


class Differs(Exception):
    pass


class ZebrooSetModel(models.AbstractModel):
    _name = "zebrooset"
    _description = "ZebrooSet"

    @api.model
    def loads(self, data):
        res = ZebrooSet._loads(data, env=self.env)
        return res

    @api.model
    def dumps(self, data):
        return ZebrooSet._dumps(None, data, env=self.env)

    @api.model
    def rs(self, data):
        return ZebrooSet(data)

    @api.model
    def _prepare_dump(self, data):
        return data

    @api.model
    def iterate(self, data, **kwparams):
        return ZebrooSet([]).iterate_data(data, **kwparams)

    @api.model
    def _prepare_load(self, data):
        if isinstance(data, models.Model):
            return data
        if isinstance(data, (str, bytes)):
            return data
        if isinstance(data, (dict, list, tuple)):
            return ZebrooSet(data)
        return data

    @api.model
    def _encode(self, obj, just_test):
        raise NotImplementedError(obj)

    @api.model
    def _decode(self, obj, just_test):
        raise NotImplementedError(obj)

    @api.model
    def get_python_type(self, obj):
        return get_python_type(obj)


class ZebrooSet(object):
    class NoRecordException(Exception):
        pass

    class TooManyrecordsException(Exception):
        pass

    def __init__(self, data):
        if isinstance(data, (_WrappedDict)):
            data = data._d
        elif isinstance(data, (_WrappedList)):
            data = data._l
        if isinstance(data, ZebrooSet):
            self._d = data._d
        elif hasattr(data, "_zbs_iterate_records"):
            self._d = data
        else:
            assert isinstance(data, (dict, list))
            self._d = data

    def __nonzero__(self):
        return self._d.__nonzero__()

    def __bool__(self):
        return bool(self._d)

    def __add__(self, other):
        if isinstance(other, ZebrooSet):
            self._d += other._d
        elif isinstance(other, list):
            self._d += other
        else:
            raise NotImplementedError()
        return self

    def _as_python_object(self):
        data = self._d

        def transform(x):
            if isinstance(x, (ZebrooSet, _WrappedList, _WrappedDict)):
                return x._as_python_object()
            return x

        if isinstance(data, list):
            data = [transform(x) for x in data]

        return data

    def _is_equal(self, other):
        def _compare_dict(one, two):
            if not isinstance(two, dict):
                raise Differs()
            keys1 = list(sorted(set(one.keys())))
            keys2 = list(sorted(set(two.keys())))
            if keys1 != keys2:
                raise Differs()
            for k, X in one.items():
                Y = two[k]
                compare(X, Y)

        def _compare_list(one, two):
            for i, x in enumerate(one):
                y = two[i]
                compare(x, y)

        def compare(one, two):
            one = get_python_type(one)
            two = get_python_type(two)
            if isinstance(one, dict):
                _compare_dict(one, two)
            elif isinstance(one, (tuple, list)):
                _compare_list(one, two)
            else:
                if one != two:
                    raise Differs()

        try:
            compare(self._d, other)
        except (Differs, KeyError):
            logger.debug(f"Do not match:\nValue1:\n{str(self)}\n\nValue2:\n{other}")
            return False
        else:
            return True

    def __setattr__(self, name, value):
        check_setattr_forbidden(name)
        if name in ["_d", "__parent__", "__root__"]:
            return super().__setattr__(name, value)
        _set_value_in_dict(self._d, name, value)

    def __getattribute__(self, name):
        if name in [
            "_d",
            "_is_equal",
            "_dumps",
            "_loads",
            "__class__",
            "__dict__",
            "_keys",
            "_wraplist",
            "__getattribute__",
            "_iterate_records",
            "_merge",
            "_as_python_object",
            "_is_scalar",
            "iterate_data",
        ]:
            res = super().__getattribute__(name)
            return res
        if isinstance(name, slice):
            return _WrappedList(self._d, self, slice=name)
        try:
            data = super().__getattribute__("_d")
        except AttributeError:
            data = None
        if name == "setdefault":
            return _WrappedDict(data, None).setdefault
        if name == "keys":
            return _WrappedDict(data, None).keys
        if name == "pop":
            return _WrappedDict(data, None).pop
        if name == "items":
            return _WrappedDict(data, None).items
        if name == "get":
            return _WrappedDict(data, None).get
        data = _wrap(data, None)
        return _Dive(data, name)

    def _is_scalar(self, value):
        return _is_scalar(value)

    def __getitem__(self, key):
        # called when ['items'], ['keys'] is called
        if key in ["items", "keys"]:
            return _Dive(self._d, key)

        return self.__getattribute__(key)

    def __setitem__(self, name, value):
        check_setattr_forbidden(name)
        _set_value_in_dict(self._d, name, value)

    def __len__(self):
        return len(self._d)

    def _wraplist(self):
        if isinstance(self._d, dict):
            self._d = [self._d]

    def _keys(self):
        return _WrappedDict(self._d)._keys()

    def _setdefault(self):
        return _WrappedDict(self._d)._setdefault()

    def _dumps(self, content=NoArg, env=None):
        return _dumps(self, content, env=env)

    @staticmethod
    def _loads(content, env):
        data = env["zebrooset"]._prepare_load(content)
        data = json.loads(content, cls=Decoder, env=env)
        if isinstance(data, (list, dict, tuple)):
            data = ZebrooSet(data)
        return data

    def iterate_data(self, data, keep_small=False):
        walk_the_lineresult = walk_the_line(data)
        if walk_the_lineresult and hasattr(walk_the_lineresult, "_zbs_iterate_records"):
            for index, record in enumerate(
                walk_the_lineresult._zbs_iterate_records(keep_small=keep_small)
            ):
                yield index, record
        elif isinstance(data, (models.Model, ZebrooSet, list, dict)):
            if isinstance(data, (list, dict)):
                data = ZebrooSet(data)
            if isinstance(data, ZebrooSet) and isinstance(data._d, dict):
                data._d = [data._d]
            if isinstance(data, ZebrooSet) and isinstance(data._d, _WrappedDict):
                data._d = [data._d]
            if isinstance(data, ZebrooSet) and isinstance(data._d, _WrappedList):
                data._d = ZebrooSet(data._l)

            assert not isinstance(data, list)
            assert not isinstance(data, dict)
            assert not isinstance(data, _WrappedList)
            assert not isinstance(data, _WrappedDict)

            if isinstance(data, models.Model):
                for index, rec in enumerate(data):
                    yield index, rec
            elif isinstance(data, ZebrooSet):
                if isinstance(data._d, list):
                    for index, rec in enumerate(data):
                        yield index, rec
                else:
                    yield 0, [data._d]
            else:
                raise NotImplementedError()
        else:
            for index, item in enumerate(data):
                yield index, item

    def _iterate_records(self, start=None, stop=None, keep_small=False):
        yield from _iterate_records(self, start=start, stop=stop, keep_small=keep_small)

    def __repr__(self):
        return repr(self._d)

    def _merge(self, d):
        self._d = _recursive_dict_merge(self._d, d)


class _WrappedList(object):
    def __init__(self, list, parent, slice=None):
        self.__parent__ = parent
        self._l = list if not slice else list[slice]

    def _dumps(self, content=NoArg, env=None):
        return _dumps(self, content, env)

    def __nonzero__(self):
        return self._l.__nonzero__()

    def __bool__(self):
        return bool(self._l)

    def _iterate_records(self, start=None, stop=None, keep_small=False):
        yield from _iterate_records(self, start=start, stop=stop, keep_small=keep_small)

    def __getattribute__(self, name):
        if name in [
            "_l",
            "__parent__",
            "__class__",
            "_dumps",
            "append",
            "index",
            "insert",
            "pop",
            "remove",
            "reverse",
            "sort",
            "_merge",
            "_iterate_records",
            "_keys",
            "get",
            "_is_scalar",
            "_as_python_object",
        ]:
            return super().__getattribute__(name)
        if name == "__root__":
            return _get_root(self)
        return _Dive(self._l, name)

    def _is_scalar(self, value):
        return _is_scalar(value)

    def _keys(self):
        return []

    def append(self, item):
        self._l.append(item)

    def index(self, item):
        self._l.index(item)

    def insert(self, index, item):
        self._l.insert(index, item)

    def pop(self, index):
        self._l.pop(index)

    def remove(self, item):
        self._l.remove(item)

    def reverse(self):
        self._l.reverse()

    def sort(self):
        self._l.sort()

    def __getitem__(self, item):
        if isinstance(item, str):
            v = _Dive(self._l, item)
        else:
            v = self._l[item]
        if isinstance(v, (dict, list)):
            return _wrap(v, self.__parent__)
        else:
            return v

    def __add__(self, other):
        return self._l + other

    def __len__(self):
        return len(self._l)

    def __setattr__(self, name, value):
        check_setattr_forbidden(name)
        if name in [
            "_l",
            "_keys",
            "__class__",
            "__parent__",
        ]:
            return super().__setattr__(name, value)
        data = self._l
        while (
            isinstance(data, (_WrappedList, list))
            and not isinstance(data, (dict, _WrappedDict, ZebrooSet))
            and len(data) == 1
        ):
            data = data[0]
        if isinstance(data, dict):
            _set_value_in_dict(data, name, value)
        else:
            raise ValueError(name)

    def _merge(self, d):
        _recursive_dict_merge(self._l, d)

    def _as_python_object(self):
        return self._l


class _WrappedDict(object):
    def __init__(self, data, parent):
        self.__parent__ = parent
        self._d = data

    def __nonzero__(self):
        return self._d.__nonzero__()

    def __bool__(self):
        return bool(self._d)

    def __repr__(self):
        return repr(self._d)

    def _setdefault(self):
        return self._d.setdefault

    def _keys(self):
        keys = self._d.keys()

        def no_meta(key):
            if isinstance(key, str):
                if key.startswith("___"):
                    return False
            return True

        keys = list(filter(no_meta, keys))
        return keys

    def __getitem__(self, key):
        res = self.__getattribute__(key)
        return res

    def __setitem__(self, name, value):
        check_setattr_forbidden(name)
        _set_value_in_dict(self._d, name, value)

    def __setattr__(self, name, value):
        check_setattr_forbidden(name)
        if name in [
            "_d",
            "_keys",
            "__class__",
            "__parent__",
            "_merge",
        ]:
            return super().__setattr__(name, value)
        _set_value_in_dict(self._d, name, value)

    def _dumps(self, content=NoArg, env=None):
        return _dumps(self, content, env=env)

    def __getattribute__(self, name):
        if name in [
            "_d",
            "_keys",
            "__class__",
            "_dumps",
            "__getattribute__",
            "_merge",
            "_as_pt",
            "_iterate_records",
            "_is_scalar",
        ]:
            return super().__getattribute__(name)
        if name == "__root__":
            return _get_root(self)
        if name in ["__parent__"]:
            v = super().__getattribute__(name)
            if isinstance(v, (dict, list)):
                return _wrap(v, v.__parent__)
            elif isinstance(v, _WrappedDict):
                return v
            elif v is None:
                return None
            else:
                raise NotImplementedError(name)
        if name in ["_d"]:
            res = super().__getattribute__(name)
            if isinstance(res, (dict, list)):
                res = _wrap(res, self.__parent__)
            return res
        if name == "setdefault":
            return self._d.setdefault
        if name == "keys":
            return self._keys
        if name == "pop":
            return self._d.pop
        if name == "get":
            return self._d.get
        if name == "items":
            return self._d.items
        if name == "_as_python_object":
            return lambda: self._d
        return _Dive(self, name)

    def _is_scalar(self, value):
        return _is_scalar(value)

    def _merge(self, d):
        _recursive_dict_merge(self._d, d)

    def _iterate_records(self, start=None, stop=None, keep_small=False):
        def _iterate():
            yield _wrap(item, None)

        if start is None and stop is None:
            yield 0, self
        else:
            for index, item in enumerate([self]):
                if start is None or index >= start:
                    if stop is None or index < stop:
                        yield index, item


def _Dive(data, name):
    parent = data

    def dive(data, name):
        if isinstance(name, int) and isinstance(data, (_WrappedList, list)):
            if isinstance(data, _WrappedList):
                data = _wrap(data._l, parent)
            return data[name]
        while (
            isinstance(data, (_WrappedList, list))
            and not isinstance(data, (dict, _WrappedDict, ZebrooSet))
            and len(data) == 1
        ):
            data = data[0]
        if isinstance(data, (_WrappedList, list)):
            if len(data) > 1:
                raise AttributeError(name)
            if not data:
                return None
        if isinstance(name, str):
            orig_name = name
            name = get_key_in_dict(data, name)
            if name is None:
                raise AttributeError(orig_name)
        elif isinstance(name, int) and isinstance(data, (_WrappedDict, dict)):
            if isinstance(data, _WrappedDict):
                res = list(data._d.keys())[name]
            else:
                res = data.keys()[name]
            return res

        if isinstance(data, _WrappedDict):
            res = data._d[name]
        else:
            res = data[name]
        if isinstance(res, (dict, list)):
            return _wrap(res, parent=parent)
        return res

    return dive(data, name)


def _wrap(data, parent=None):
    if isinstance(data, dict):
        return _WrappedDict(data, parent)
    elif isinstance(data, (_WrappedDict, _WrappedList)):
        return data
    elif isinstance(data, (list, tuple)):
        return _WrappedList(data, parent)
    elif isinstance(data, str):
        return _WrappedList([data], parent)
    elif data is None:
        return [data]
    elif hasattr(data, "_zebrooset_wrap"):
        return data._zebrooset_wrap()
    else:
        return data


def lowify_keys(keys):
    for x in keys:
        if isinstance(x, str):
            x = x.lower()
        yield x


def get_key_in_dict(data, key):
    if isinstance(key, str):
        data = walk_the_line(data)
    if isinstance(data, dict):
        keys = list(data.keys())
    elif isinstance(data, _WrappedDict):
        keys = list(data._d.keys())
    else:
        raise AttributeError(key)
    lower_keys = list(lowify_keys(keys))
    lower_key = key
    if isinstance(key, str):
        lower_key = lower_key.lower()
    if lower_key in lower_keys:
        return keys[lower_keys.index(lower_key)]
    else:
        return None


def _set_value_in_dict(dict, key, value):
    real_key = get_key_in_dict(dict, key)
    if real_key is not None and real_key != key:
        raise ValueError(f"Would result in duplicate key: exists {real_key} vs. {key}")
    if real_key is None:
        real_key = key

    if isinstance(dict, (_WrappedDict, list)) and not isinstance(key, int):
        dict = walk_the_line(dict)
    dict[real_key] = value


def _get_root(rs):
    p = rs
    while p.__parent__ is not None:
        p = p.__parent__
    return p


def check_setattr_forbidden(name):
    pass


def repr(data):
    try:
        s = json.dumps(data, indent=4, cls=Encoder)
    except Exception:
        s = data.__repr__()
    return s


class Encoder(json.JSONEncoder):
    """Encode Odoo recordsets so that we can later recompose them"""

    def __init__(self, *args, **kwargs):
        self.env = None
        env = kwargs.pop("env", None)
        super().__init__(*args, **kwargs)
        if env:
            self.env = env

    def default(self, obj):
        if isinstance(obj, ZebrooSet):
            return obj._d
        elif isinstance(obj, _WrappedDict):
            return obj._d
        elif isinstance(obj, _WrappedList):
            return obj._l
        elif isinstance(obj, models.BaseModel):
            return {
                "_type": "odoo_recordset",
                "model": obj._name,
                "ids": obj.ids,
                "uid": obj.env.uid,
                "su": obj.env.su,
                "context": self._get_record_context(obj),
            }
        elif isinstance(obj, bytes):
            return {"_type": "bytes", "value": base64.b64encode(obj).decode("ascii")}
        elif isinstance(obj, uuid.UUID):
            return {"_type": "uuid", "value": str(obj)}
        elif isinstance(obj, datetime):
            return {"_type": "datetime_isoformat", "value": obj.isoformat()}
        elif isinstance(obj, date):
            return {"_type": "date_isoformat", "value": obj.isoformat()}
        elif isinstance(obj, time):
            return {"_type": "time_isoformat", "value": obj.isoformat()}
        elif isinstance(obj, lxml.etree._Element):
            return {
                "_type": "etree_element",
                "value": lxml.etree.tostring(obj, encoding=str),
            }
        elif isinstance(obj, Decimal):
            return {"_type": "Decimal", "value": json.dumps(float(obj), cls=Encoder)}
        elif type(obj).__name__ == "ComponentRegistry":
            return {"_type": "remove"}
        elif type(obj).__name__ == "Logger":
            return {"_type": "remove"}
        elif type(obj).__name__ == "function":
            return {"_type": "remove"}
        elif isinstance(obj, _WrappedDict):
            return obj._d
        elif isinstance(obj, Path):
            return {"_type": "pathlib.Path", "value": str(obj)}
        elif isinstance(obj, _WrappedList):
            return obj._l
        elif isinstance(obj, models.NewId):
            return obj.origin

        try:
            testresult = self.env and self.env["zebrooset"]._encode(obj, just_test=True)
        except:
            pass
        else:
            if testresult:
                return self.env["zebrooset"]._encode(obj)

        return json.JSONEncoder.default(self, obj)

    def _get_record_context(self, obj):
        if not hasattr(obj, "_job_prepare_context_before_enqueue"):
            return {}
        return obj._job_prepare_context_before_enqueue()


class Decoder(json.JSONDecoder):
    """Decode json, recomposing recordsets"""

    def __init__(self, *args, **kwargs):
        self.env = None
        env = kwargs.pop("env", None)
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
        if env:
            self.env = env

    def object_hook(self, obj):
        if "_type" not in obj:
            return obj
        type_ = obj["_type"]
        if type_ == "ZebrooSet":
            data = json.loads(obj["data"], cls=Decoder, env=self.env)
            return ZebrooSet(data)
        elif type_ == "WrappedDict":
            data = json.loads(obj["data"], cls=Decoder, env=self.env)
            return _WrappedDict(data)
        elif type_ == "WrappedList":
            data = json.loads(obj["data"], cls=Decoder, env=self.env)
            return _WrappedList(data)
        elif type_ == "odoo_recordset":
            model = self.env(user=obj.get("uid"), su=obj.get("su"))[obj["model"]]
            if obj.get("context"):
                model = model.with_context(**obj.get("context", {}))
            return model.browse(obj["ids"])
        elif type_ == "pathlib.Path":
            return Path(obj["value"])
        elif type_ == "datetime_isoformat":
            return dateutil.parser.parse(obj["value"])
        elif type_ == "date_isoformat":
            return dateutil.parser.parse(obj["value"]).date()
        elif type_ == "time_isoformat":
            return time.fromisoformat(obj["value"])
        elif type_ == "etree_element":
            return lxml.etree.fromstring(obj["value"])
        elif type_ == "bytes":
            return base64.b64decode(obj["value"].encode("ascii"))
        elif type_ == "uuid":
            return uuid.UUID(obj["value"])
        elif type_ == "Decimal":
            return Decimal(obj["value"])
        elif type_ == "remove":
            return False

        if self.env["zebrooset"]._decode(obj, just_test=True):
            return self.env["zebrooset"]._decode(obj)

        return obj


def _recursive_dict_merge(d1, d2):
    def conv(d):
        if isinstance(d, (ZebrooSet, _WrappedDict)):
            d = d._d
        elif isinstance(d, _WrappedList):
            d = d._l
        return d

    orig_d1 = d1
    d1 = walk_the_line(conv(d1))
    d2 = walk_the_line(conv(d2))

    for k, v2 in d2.items():
        v1 = d1.get(k)
        if isinstance(v1, dict) and isinstance(v2, dict):
            _recursive_dict_merge(v1, v2)
        elif isinstance(v1, list) and isinstance(v2, list):
            _recursive_dict_merge(v1, v2)
        else:
            d1[k] = v2

    return orig_d1


def _iterate_records(self, start=None, stop=None, keep_small=False):
    def _iterate():
        for index, item in ZebrooSet([]).iterate_data(self._as_python_object()):
            if isinstance(item, str) or item is None:
                pass
            else:
                item = _wrap(item, None)
            yield index, item

    if start is None and stop is None:
        yield from _iterate()
    else:
        for index, item in enumerate(_iterate()):
            if start is None or index >= start:
                if stop is None or index < stop:
                    yield index, item
