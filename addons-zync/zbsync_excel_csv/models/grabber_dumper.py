# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, fields, models
from odoo.exceptions import UserError
import io
import csv
import openpyxl

SEL_CONTENT_TYPES = [("csv", "CSV"), ("excel", "Excel")]

DEFAULT_MAX_COL_COUNT = 1000


class Mixin(models.AbstractModel):
    _name = "zbs.csvexcel.mixin"
    _description = "CSV/Excel Mixin (Abstract)"

    type = fields.Selection(SEL_CONTENT_TYPES, string="Type")
    fieldnames = fields.Char("Field names comma separated")
    csv_delimiter = fields.Char("CSV Delimiter", default=";")
    max_column_count = fields.Integer("Max Column Count")
    sample_file = fields.Binary("Sample File")
    encoding_id = fields.Many2one("zbs.encoding", "Encoding")
    sheet_name = fields.Char("Sheet Name")
    last_error = fields.Char("Last Error")

    def generate_mapper(self):
        if not self.sample_file:
            raise UserError(_("Please upload a sample file"))
        raise NotImplementedError("generate mapper")


class CSVGrabber(models.Model):
    _inherit = ["zbs.grabber", "zbs.csvexcel.mixin"]
    _name = "zbs.grabber.csvexcel"
    _description = "CSV / Excel Grabber"

    first_line_of_data = fields.Integer(default=1)
    data_contains_headers = fields.Boolean(default=True)

    def process_record(self, instance, index, record, data, errors=None):
        if not record:
            return

        if self.type == "csv":
            res = self._read_csv(record)
        elif self.type == "excel":
            res = self._read_excel(record)
        else:
            raise NotImplementedError(self.type)
        return res

    def _get_fieldnames(self):
        res = list(map(lambda x: x.strip(), (self.fieldnames or "").split(",")))
        return res

    def _read_csv(self, content):
        content = self._extract_content(content)
        stream = self._get_stream(content, requires="str")
        csv_reader = csv.reader(stream, delimiter=self.csv_delimiter)
        records = []
        fieldnames = None
        for i, row in enumerate(csv_reader):
            if i < (self.first_line_of_data - 1):
                continue
            if fieldnames is None and self.data_contains_headers:
                fieldnames = []
                for t in row:
                    fieldnames.append(t)
                continue
            elif fieldnames is None:
                fieldnames = self._get_fieldnames()
            data = {}
            for i, fieldname in enumerate(fieldnames):
                try:
                    data[fieldname] = row[i]
                except Exception as e:
                    self.last_error = e
                    continue
            records.append(data)
        return records

    def _read_excel(self, content):
        content = self._extract_content(content)
        stream = self._get_stream(content)
        #encoding = self._get_encoding()
        wb = openpyxl.load_workbook(stream, data_only=True, read_only=True)
        #wb =  wb.encode(encoding)
        if self.sheet_name:
            ws = wb[self.sheet_name]
        else:
            ws = wb.active
        keys = None
        records = []
        max_cols = self.max_column_count or DEFAULT_MAX_COL_COUNT
        for idx, row in enumerate(
            ws.iter_rows(min_row=1, min_col=1, max_row=99999999, max_col=max_cols)
        ):
            if idx < (self.first_line_of_data - 1):
                continue
            if keys is None and self.data_contains_headers:
                keys = [x.value for x in row]
                continue
            elif not self.data_contains_headers:
                keys = self._get_fieldnames()

            record = {keys[i]: x.value for i, x in enumerate(row) if len(keys) > i}
            if any(record.values()):
                records.append(record)
        return records


class CSVDumper(models.Model):
    _inherit = ["zbs.dumper", "zbs.csvexcel.mixin"]
    _name = "zbs.dumper.csvexcel"
    _description = "CSV / Excel Dumper"

    first_line_headers = fields.Boolean("First Line Headers", default=True)

    def process(self, instance, data, errors=None):
        if self.type == "csv":
            content = self._write_csv(data)
            encoding = self._get_encoding()
            if encoding:
                content = content.encode(encoding)

        elif self.type == "excel":
            content = self._write_excel(data)
        else:
            raise NotImplementedError(self.type)

        keep = self._keep_input(0, data, data)
        return instance.Result(
            {
                "content": content,
                "data": keep,
            }
        )

    def _write_csv(self, records):
        stream = io.StringIO()
        csv_writer = csv.writer(stream, delimiter=self.csv_delimiter)
        if self.fieldnames:
            fieldnames = [x.strip() for x in self.fieldnames.split(",")]
        else:
            fieldnames = None
        for i, record in records._iterate_records():
            if not i and fieldnames is None:
                fieldnames = list(record.keys())

            if not i and self.first_line_headers:
                csv_writer.writerow(fieldnames)
            csv_writer.writerow([record[x] for x in fieldnames])
        stream.seek(0)
        res = stream.getvalue()
        return res

    def _write_excel(self, records):
        workbook = openpyxl.Workbook()

        # Get the active sheet in the workbook
        sheet = workbook.active

        row = 1
        fieldnames = None

        def _get_fieldnames(record):
            return (
                self.fieldnames.split(",") if self.fieldnames else list(record.keys())
            )

        _, first_record = next(records._iterate_records())
        if first_record and fieldnames is None:
            fieldnames = _get_fieldnames(first_record)

        if self.first_line_headers:
            for col_num, fieldname in enumerate(fieldnames, 1):
                cell = sheet.cell(row=row, column=col_num)
                cell.value = fieldname
            row += 1

        for row_num, (_, row_data) in enumerate(records._iterate_records(), row):
            for col_num, fieldname in enumerate(fieldnames, 1):
                cell = sheet.cell(row=row_num, column=col_num)
                cell.value = row_data[fieldname]

        # Save the workbook
        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return stream.getvalue()
