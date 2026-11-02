# -*- coding: utf-8 -*-
# Author: Moritz Kern
import calendar
import csv
import io

from odoo import fields, models, _
from odoo.exceptions import UserError


class FischbacherDatevRow(models.Model):
    """Legacy model: preserve existing row numbers without changing them."""
    _name = "fischbacher.datev.row"
    _description = "Dauerhafte DATEV-Monatslaufnummer (Altbestand)"
    _order = "month, number, id"

    company_id = fields.Many2one("res.company", required=True, ondelete="restrict", index=True)
    move_id = fields.Many2one("account.move", required=True, ondelete="restrict", index=True)
    month = fields.Date(required=True, index=True)
    row_index = fields.Integer(required=True)
    number = fields.Integer(required=True)
    fingerprint = fields.Char(required=True)

    _identity_unique = models.Constraint(
        "UNIQUE(move_id, row_index)", "Diese Exportzeile ist bereits nummeriert."
    )
    _number_unique = models.Constraint(
        "UNIQUE(company_id, month, number)", "Die Monatsnummer ist bereits vergeben."
    )
    _positive_number = models.Constraint("CHECK(number > 0)", "Die Nummer muss positiv sein.")


class FischbacherDatevMoveNumber(models.Model):
    _name = "fischbacher.datev.move.number"
    _description = "Dauerhafte firmenweite DATEV-Monatsnummer je Buchung"
    _order = "company_id, month, number, id"

    company_id = fields.Many2one("res.company", required=True, ondelete="restrict", index=True)
    move_id = fields.Many2one("account.move", required=True, ondelete="restrict", index=True)
    month = fields.Date(required=True, index=True)
    number = fields.Integer(required=True)

    _move_unique = models.Constraint(
        "UNIQUE(move_id)", "Dieser Buchung ist bereits eine Monatsnummer zugeordnet."
    )
    _number_unique = models.Constraint(
        "UNIQUE(company_id, month, number)", "Die Monatsnummer ist bereits vergeben."
    )
    _positive_number = models.Constraint("CHECK(number > 0)", "Die Nummer muss positiv sein.")


class AccountGeneralLedgerReportHandlerMonthly(models.AbstractModel):
    _inherit = "account.general.ledger.report.handler"

    def _l10n_de_datev_get_csv(self, options, moves):
        if not moves:
            return super()._l10n_de_datev_get_csv(options, moves)

        company = self.env.company
        if any(move.company_id != company or move.state != "posted" for move in moves):
            raise UserError(_(
                "Die Monatsnummerierung unterstützt nur gebuchte Buchungen "
                "der aktuellen Firma."
            ))

        # Serialize allocation for this company until the transaction ends.
        self.env.cr.execute(
            "SELECT id FROM res_company WHERE id = %s FOR UPDATE", [company.id]
        )
        Registry = self.env["fischbacher.datev.move.number"].sudo()
        Registry.invalidate_model()
        Move = self.env["account.move"].sudo().with_context(active_test=False)
        months = sorted({move.date.replace(day=1) for move in moves})
        numbers = {}

        for month in months:
            end = month.replace(day=calendar.monthrange(month.year, month.month)[1])
            monthly_moves = Move.search([
                ("company_id", "=", company.id),
                ("state", "=", "posted"),
                ("date", ">=", month),
                ("date", "<=", end),
            ], order="date, id")

            saved = Registry.search([
                ("company_id", "=", company.id), ("month", "=", month),
            ])
            # Also detect previously numbered moves transferred into this month.
            related = Registry.search([("move_id", "in", monthly_moves.ids)])
            for record in saved | related:
                move = record.move_id
                if (move.company_id != record.company_id
                        or move.date.replace(day=1) != record.month):
                    raise UserError(_(
                        "DATEV: Firma oder Buchungsmonat der bereits nummerierten "
                        "Buchung %s wurde geändert. Export abgebrochen."
                    ) % move.display_name)

            existing = {record.move_id.id: record for record in saved}
            next_number = max(saved.mapped("number"), default=0)
            values = []
            for move in monthly_moves:
                record = existing.get(move.id)
                if record:
                    numbers[move.id] = record.number
                else:
                    next_number += 1
                    numbers[move.id] = next_number
                    values.append({
                        "company_id": company.id,
                        "move_id": move.id,
                        "month": month,
                        "number": next_number,
                    })
            if values:
                Registry.create(values)

        output = io.StringIO()
        writer = csv.writer(
            output, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC
        )
        parent = super(AccountGeneralLedgerReportHandlerMonthly, self)
        reference_columns = None
        column_index = None

        # Render each selected move to retain an unambiguous move -> CSV mapping.
        for move in moves:
            text = parent._l10n_de_datev_get_csv(options, move)
            parsed = list(csv.reader(io.StringIO(text), delimiter=";", quotechar='"'))
            if len(parsed) < 2:
                raise UserError(_(
                    "DATEV: Ungültiger CSV-Kopf für Buchung %s."
                ) % move.display_name)

            columns = parsed[1]
            if reference_columns is None:
                reference_columns = columns
                try:
                    column_index = columns.index("Belegfeld 2")
                except ValueError:
                    raise UserError(_("DATEV: Die Spalte 'Belegfeld 2' fehlt."))
                writer.writerows(parsed[:2])
            elif columns != reference_columns:
                raise UserError(_("DATEV: Unterschiedliche CSV-Spalten im Export."))

            for row in parsed[2:]:
                if not row:
                    continue
                if len(row) != len(reference_columns):
                    raise UserError(_(
                        "DATEV: Ungültige CSV-Zeilenlänge für Buchung %s."
                    ) % move.display_name)
                row[column_index] = str(numbers[move.id])
                writer.writerow(row)

        return output.getvalue()
