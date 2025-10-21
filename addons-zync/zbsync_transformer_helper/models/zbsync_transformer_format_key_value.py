# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).

from odoo import fields, models


class Transformer(models.Model):
    _inherit = "zbs.transformer"
    _name = "zbs.transformer.keyvaluepair"
    _description = "Key Value Transformer"
    _help = (
        "Handles Key Value Pair Logic for external Sources to handle them like fields"
    )

    direction = fields.Selection(
        [
            ("keyvaluetodict", "Key Value to Dictionary"),
            ("dicttokeyvalue", "Dictionary to Key Value"),
        ]
    )
    fieldname = fields.Char("Field Name")
    key_name = fields.Char("Key Name")
    value_name = fields.Char("Value Name")

    def process(self, instance, data, errors=None):

        if self.direction == "keyvaluetodict":
            for r in data:
                self.recursive_replace(r, self.fieldname)
        else:
            raise NotImplementedError()
        data = super().process(instance, data, errors=errors)
        return data

    def process_record(self, instance, index, record, data, errors=None):
        self.recursive_replace(record, self.fieldname)
        return record

    def recursive_replace(self, search_dict, field):
        if not isinstance(search_dict, dict):
            search_dict = search_dict._d
        for key, value in search_dict.copy().items():
            if key == field:
                search_dict.pop(key)
                newd = key + "Transformed"
                search_dict[newd] = self.transfer_value(value)
            elif isinstance(value, dict):
                self.recursive_replace(value, field)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self.recursive_replace(item, field)

    def transfer_value(self, i):
        if isinstance(i, list):
            val = []
            for entry in i:
                val.append(self.create_new_dict(entry))
        elif isinstance(i, dict):
            val = self.create_new_dict(i)
        else:
            raise NotImplementedError()
        return val

    def create_new_dict(self, entry):
        ndict = {}
        if "Key" not in entry:
            return False
        ndict[entry[self.key_name]] = entry[self.value_name]
        return ndict
