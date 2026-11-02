import csv
import io
import math
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


def parse_row(line, delimiter):
    row = next(csv.reader(
        [line.rstrip("\r\n")], delimiter=delimiter, strict=True,
    ))
    if len(row) == 10 and not row[-1].strip():
        row.pop()
    if len(row) != 9:
        raise ValueError("9 Spalten erwartet; optional ein leeres Feld am Ende.")
    return [value.strip() for value in row]


def parse_number(text):
    text = text.strip().replace("€", "").replace("\u00a0", "").replace(" ", "")
    if not text:
        raise ValueError("Leeres Zahlenfeld; für Null bitte 0,00 verwenden.")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("Ungültige Zahl.")
    return value


def parse_date(text):
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("Datum muss TT.MM.JJJJ oder JJJJ-MM-TT sein.")


class ImportError(models.Model):
    _name = "product.history.import.error"
    _description = "Abwertungsimport: Fehler"
    _order = "line_number, id"

    job_id = fields.Many2one(
        "product.history.import.job", required=True, ondelete="cascade", index=True,
    )
    line_number = fields.Integer(string="Dateizeile")
    message = fields.Text(string="Fehler")
    original = fields.Text(string="Originalzeile")


class ImportJob(models.Model):
    _name = "product.history.import.job"
    _description = "Abwertungstabellen: Hintergrundimport"
    _order = "id desc"

    name = fields.Char(string="Bezeichnung", required=True, default="ERP-Abwertungsimport")
    file_data = fields.Binary(string="CSV-Datei", attachment=True)
    filename = fields.Char(string="Dateiname")
    source = fields.Char(string="Quellsystem", default="legacy_erp", required=True)
    batch_size = fields.Integer(string="Zeilen pro Paket", default=2000, required=True)
    delimiter = fields.Selection(
        [(";", "Semikolon"), (",", "Komma"), ("\t", "Tabulator")],
        string="Trennzeichen", default=";", required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Entwurf"), ("queued", "In Warteschlange"),
            ("running", "Läuft"), ("paused", "Pausiert"),
            ("done", "Abgeschlossen"), ("failed", "Technischer Fehler"),
        ],
        default="draft", index=True, required=True,
    )
    offset = fields.Char(default="0", readonly=True)
    processed = fields.Integer(string="Verarbeitet", readonly=True)
    created_count = fields.Integer(string="Neu angelegt", readonly=True)
    skipped_count = fields.Integer(string="Übersprungen (Altversion)", readonly=True)
    error_count = fields.Integer(string="Fehlerhafte Zeilen", readonly=True)
    last_error = fields.Text(string="Technischer Fehler", readonly=True)
    started_at = fields.Datetime(string="Gestartet", readonly=True)
    finished_at = fields.Datetime(string="Abgeschlossen", readonly=True)
    error_ids = fields.One2many(
        "product.history.import.error", "job_id", string="Fehlerprotokoll",
    )

    @api.constrains("batch_size")
    def _check_size(self):
        for job in self:
            if not 100 <= job.batch_size <= 5000:
                raise ValidationError("Paketgröße muss zwischen 100 und 5000 liegen.")

    def write(self, vals):
        protected = {"file_data", "filename", "source", "delimiter"}
        if protected.intersection(vals) and any(job.state != "draft" for job in self):
            raise UserError("Datei und Format nach Start nicht ändern; neuen Auftrag anlegen.")
        return super().write(vals)

    def _raw_file(self):
        self.ensure_one()
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name), ("res_id", "=", self.id),
                ("res_field", "=", "file_data"),
            ], limit=1,
        )
        if not attachment:
            raise UserError("CSV hochladen und Auftrag speichern.")
        return attachment.raw

    def _header_end(self, raw):
        end = raw.find(b"\n")
        first = raw if end < 0 else raw[:end + 1]
        if not first:
            raise UserError("Datei ist leer.")
        try:
            parse_row(first.decode("utf-8-sig"), self.delimiter)
        except (ValueError, UnicodeError, csv.Error) as exc:
            raise UserError("Ungültige UTF-8-Kopfzeile: %s" % exc) from exc
        return len(first)

    def _trigger_cron(self):
        self.env.ref("fischbacher_inventory_history.cron_history_import")._trigger()

    def action_start(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Nur Entwürfe starten.")
        if not (self.filename or "").lower().endswith(".csv"):
            raise UserError("Excel als CSV UTF-8 exportieren; kein direkter XLSX-Import.")
        offset = self._header_end(self._raw_file())
        self.write({
            "offset": str(offset), "state": "queued",
            "started_at": fields.Datetime.now(), "last_error": False,
        })
        self._trigger_cron()

    def action_pause(self):
        for job in self:
            if job.state in ("queued", "running"):
                job.state = "paused"

    def action_resume(self):
        for job in self:
            if job.state in ("paused", "failed"):
                job._header_end(job._raw_file())
                job.write({"state": "queued", "last_error": False})
        self._trigger_cron()

    def _error_values(self, line_number, original, message):
        return {
            "job_id": self.id, "line_number": line_number,
            "message": str(message), "original": original[:4000],
        }

    def _run_batch(self, raw):
        self.ensure_one()
        stream = io.BytesIO(raw)
        stream.seek(int(self.offset or 0))
        lines = []
        for _ in range(self.batch_size):
            line = stream.readline()
            if not line:
                break
            lines.append(line)
        parsed, errors = [], []
        for position, line in enumerate(lines):
            line_number = self.processed + position + 2
            original = line.decode("utf-8", errors="replace").rstrip("\r\n")
            try:
                row = parse_row(line.decode("utf-8"), self.delimiter)
                if "." not in row[0]:
                    raise ValueError("Externe Varianten-ID muss Modul.Name enthalten.")
                date = parse_date(row[2])
                if not row[3]:
                    raise ValueError("Lager fehlt.")
                amounts = [parse_number(value) for value in row[4:]]
                parsed.append((line_number, original, row, date, amounts))
            except (ValueError, UnicodeError, csv.Error) as exc:
                errors.append(self._error_values(line_number, original, exc))

        modules = list({entry[2][0].split(".", 1)[0] for entry in parsed})
        names = list({entry[2][0].split(".", 1)[1] for entry in parsed})
        identifiers = self.env["ir.model.data"]
        if parsed:
            identifiers = identifiers.search([
                ("module", "in", modules), ("name", "in", names),
                ("model", "=", "product.product"),
            ])
        mapping = {
            record.module + "." + record.name: record.res_id
            for record in identifiers
        }
        products = (
            self.env["product.product"].with_context(active_test=False)
            .browse(list(set(mapping.values()))).exists()
        )
        templates = {product.id: product.product_tmpl_id.id for product in products}
        pending = []
        for line_number, original, row, date, amounts in parsed:
            product_id = mapping.get(row[0])
            if product_id not in templates:
                errors.append(self._error_values(
                    line_number, original, "Variante nicht gefunden: " + row[0],
                ))
                continue
            pending.append({
                "product_id": product_id,
                "product_tmpl_id": templates[product_id],
                "date": date, "warehouse": row[3],
                "quantity": amounts[0], "purchase_price": amounts[1],
                "value": amounts[2], "base_purchase_price": amounts[3],
                "total_value": amounts[4], "legacy_article_number": row[1],
            })
        if pending:
            self.env["product.inventory.history"].create(pending)
        if errors:
            self.env["product.history.import.error"].create(errors)
        finished = stream.tell() >= len(raw)
        self.write({
            "offset": str(stream.tell()),
            "processed": self.processed + len(lines),
            "created_count": self.created_count + len(pending),
            "error_count": self.error_count + len(errors),
            "state": "done" if finished else "running",
            "finished_at": fields.Datetime.now() if finished else False,
        })
        return len(lines)

    @api.model
    def _cron_import(self):
        self.env.cr.execute(
            "SELECT id FROM product_history_import_job "
            "WHERE state IN ('queued', 'running') "
            "ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED"
        )
        result = self.env.cr.fetchone()
        if not result:
            return
        job = self.browse(result[0])
        try:
            raw = job._raw_file()
            job._header_end(raw)
            with self.env.cr.savepoint():
                count = job._run_batch(raw)
        except Exception as exc:
            job.invalidate_recordset()
            job.write({"state": "failed", "last_error": str(exc)[:4000]})
            return
        self.env["ir.cron"]._commit_progress(
            count, remaining=0 if job.state == "done" else 1,
        )
