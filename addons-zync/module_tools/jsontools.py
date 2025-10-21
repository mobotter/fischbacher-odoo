import json
from odoo.tools.func import lazy
import uuid
import base64
import dateutil
from datetime import datetime, date
import lxml
from decimal import Decimal
from odoo import models
from requests.structures import CaseInsensitiveDict


def encode_json(data):
    return json.dumps(data, cls=JobEncoder)

def decode_json(data, env):
    return json.loads(data, cls=JobDecoder, env=env)

class JobEncoder(json.JSONEncoder):
    """Encode Odoo recordsets so that we can later recompose them"""

    def _get_record_context(self, obj):
        return obj._job_prepare_context_before_enqueue()

    def default(self, obj):
        if isinstance(obj, models.BaseModel):
            return {
                "_type": "odoo_recordset",
                "model": obj._name,
                "ids": obj.ids,
                "uid": obj.env.uid,
                "su": obj.env.su,
                "context": self._get_record_context(obj),
            }
        elif isinstance(obj, bytes):
            return {"_type": "bytes", "value": base64.b64encode(obj).decode('ascii')}
        elif isinstance(obj, uuid.UUID):
            return {"_type": "uuid", "value": str(obj)}
        elif isinstance(obj, datetime):
            return {"_type": "datetime_isoformat", "value": obj.isoformat()}
        elif isinstance(obj, date):
            return {"_type": "date_isoformat", "value": obj.isoformat()}
        elif isinstance(obj, lxml.etree._Element):
            return {
                "_type": "etree_element",
                "value": lxml.etree.tostring(obj, encoding=str),
            }
        elif isinstance(obj, CaseInsensitiveDict):
            return {"_type": "CaseInsensitiveDict", "value": json.dumps(dict(obj), cls=JobEncoder)}
        elif isinstance(obj, Decimal):
            return {"_type": "Decimal", "value": json.dumps(float(obj), cls=JobEncoder)}
        elif type(obj).__name__ == 'ComponentRegistry':
            return {"_type": "remove"}
        elif type(obj).__name__ == 'Logger':
            return {"_type": "remove"}
        elif type(obj).__name__ == 'function':
            return {"_type": "remove"}
        elif isinstance(obj, lazy):
            return obj._value
        return json.JSONEncoder.default(self, obj)


class JobDecoder(json.JSONDecoder):
    """Decode json, recomposing recordsets"""

    def __init__(self, *args, **kwargs):
        env = kwargs.pop("env", None)
        super().__init__(object_hook=self.object_hook, *args, **kwargs)
        if env:
            self.env = env

    def object_hook(self, obj):
        if "_type" not in obj:
            return obj
        type_ = obj["_type"]
        if type_ == "odoo_recordset":
            model = self.env(user=obj.get("uid"), su=obj.get("su"))[obj["model"]]
            if obj.get("context"):
                model = model.with_context(**obj.get("context"))
            return model.browse(obj["ids"])
        elif type_ == "datetime_isoformat":
            return dateutil.parser.parse(obj["value"])
        elif type_ == "date_isoformat":
            return dateutil.parser.parse(obj["value"]).date()
        elif type_ == "etree_element":
            return lxml.etree.fromstring(obj["value"])
        elif type_ == "bytes":
            return base64.b64decode(obj['value'].encode('ascii'))
        elif type_ == "CaseInsensitiveDict":
            return CaseInsensitiveDict(json.loads(obj['value'], cls=JobDecoder, env=self.env))
        elif type_ == "uuid":
            return uuid.UUID(obj['value'])
        elif type_ == "Decimal":
            return Decimal(obj['value'])
        elif type_ == "remove":
            return False

        return obj