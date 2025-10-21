# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from io import BytesIO, StringIO
from odoo import models
from odoo.exceptions import ValidationError
from odoo.addons.zbsync.models.zebrooset import ZebrooSet, _WrappedDict


class GrabberDumper(models.AbstractModel):
    _name = "zbs.grabber_dumper"
    _description = "Grabber / Dumper (Abstract, Common Functions)"

    def _extract_content(self, content):
        if isinstance(content, ZebrooSet) and isinstance(
            content._as_python_object(), list
        ):
            d = content._as_python_object()
            if len(d) == 1:
                content = d[0]
        if isinstance(content, (dict, _WrappedDict, ZebrooSet)):
            if "filecontent" in content:
                content = content["filecontent"]
            elif "content" in content:
                content = content["content"]
        return content

    def _get_encoding(self):
        if "encoding" in self._fields.keys():
            return self["encoding"]
        if "encoding_id" in self._fields.keys():
            return self.encoding_id.name
        return None

    def _get_stream(self, content, requires=None):
        if isinstance(content, bytes) and requires == "str":
            encoding = self._get_encoding()
            if not encoding and requires:
                raise ValidationError("Please provide an encoding!")
            if encoding:
                content = content.decode(encoding)

        if isinstance(content, bytes):
            stream = BytesIO(content)
        elif isinstance(content, str):
            stream = StringIO(content)
        else:
            raise NotImplementedError(content)
        return stream
