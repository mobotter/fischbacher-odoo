# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models, fields
from lxml import etree
import tempfile
import os
from pathlib import Path


class CodeHelperMixin(models.Model):
    _name = "code.helper.mixin"
    _description = "Code Helper Mixin"

    code_helper = fields.Many2one("zbs.transformer.helper", "Helper")
    code_helper_description = fields.Char(
        related="code_helper.description", string="Code Helper Description"
    )

    def append_code_helper(self):
        for rec in self:
            if not rec.code_helper:
                raise UserWarning("Please enter Helper first!")
            x = "" if not rec.code else "\n"
            rec.code = x + (rec.code or "") + rec.code_helper.code
            rec.code_helper = False


class ZbsyncTransformerHelper(models.Model):
    _name = "zbs.transformer.helper"
    _description = "Zync Transformer Helper"

    name = fields.Char("Name")
    description = fields.Char("Description")
    code = fields.Char("Code")

    def create_data_file(self, ids):
        odoo = etree.Element("odoo")
        data = etree.Element("data")
        for id in self.browse(ids):
            mod = f"helper-{id.id}"
            recattr = {"id": mod, "model": "zbs.transformer.helper"}
            record = etree.Element("record", attrib=recattr)
            nameattr = {"name": "name"}
            name = etree.SubElement(record, "field", attrib=nameattr)
            name.text = id.name or ""
            nameattr["name"] = "description"
            desc = etree.SubElement(record, "field", attrib=nameattr)
            desc.text = id.description or ""
            nameattr["name"] = "code"
            code = etree.SubElement(record, "field", attrib=nameattr)
            code.text = id.code or ""
            data.append(record)
        odoo.append(data)
        t = etree.tostring(odoo).decode("utf-8")
        return t

    def _get_xml(self, ids):
        parent_dir = Path(tempfile.mktemp(suffix=".xml"))
        parent_dir.mkdir(exist_ok=True, parents=True)
        filepath = parent_dir / "helpers.xml"
        os.chdir(parent_dir)
        with open("helpers.xml", "w+") as f:
            content = self.create_data_file(ids)
            f.write(content)
        return filepath.read_bytes()

    def download(self):
        ids = self.ids
        str_ids = ",".join(map(str, ids))
        return {
            "type": "ir.actions.act_url",
            "url": f"/zync/transformer_helper/download?ids={str_ids}",
            "target": "self",
        }
