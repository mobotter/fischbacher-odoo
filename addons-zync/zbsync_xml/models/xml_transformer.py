# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import base64
import xmltodict
from odoo import api, fields, models


class PythonTransformer(models.Model):
    _inherit = ["zbs.transformer", "zbs.grabber"]
    _name = "zbs.transformer.xml"
    _description = "XML"

    propagate_code_result = fields.Boolean(default=True)
    ttype = fields.Selection(
        [
            ("xml2dict", "xml2dict"),
            ("dict2xml", "dict2xml"),
            ("dict2xmlb64", "dict2xml as Base64"),
            ("lxml2dict", "lxml2dict (experimental - uses less RAM)"),
        ],
        string="Type",
    )
    root_element_name = fields.Char(
        "Root Element Name",
        default="data",
        required=False,
        help="If not given, then content is rendered as is as string",
    )
    show_ui_root_element = fields.Boolean(compute="_compute_show_ui_root_element")

    @api.depends("ttype")
    def _compute_show_ui_root_element(self):
        for rec in self:
            rec.show_ui_root_element = "2xml" in (rec.ttype or "")

    def _do_exec(self, record, data, index, instance, errors=None):
        from .lxml_transformer import lxml_xml_string_to_dict

        root_name = self.root_element_name

        content = self._extract_content(record)
        if not content:
            result = {}
        elif self.ttype == "xml2dict":
            content = content.decode("utf-8")
            result = xmltodict.parse(content)

        elif self.ttype in ["dict2xml", "dict2xmlb64"]:
            if isinstance(content, bytearray):
                content = content.decode("utf-8")

            content = xmltodict.unparse({root_name: content}, pretty=True)
            content = self._process_xml(content)
            if self.ttype in ["dict2xmlb64"]:
                content = base64.b64encode(content.encode("utf8"))
            result = {"content": content}

        elif self.ttype == "lxml2dict":
            result = lxml_xml_string_to_dict(content)
        else:
            raise NotImplementedError(self.ttype)
        return result

    def _process_xml(self, xmlstring):
        if not self.root_element_name:
            xmlstring = xmlstring.split("<>", 1)[1]
            xmlstring = xmlstring.rsplit("</>", 1)[0]
        return xmlstring
