# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import csv
import io
from collections import defaultdict
from datetime import datetime

from odoo import fields, models
from odoo.tools import float_compare, float_repr


class AccountGeneralLedgerReportHandler(models.AbstractModel):
    _inherit = "account.general.ledger.report.handler"

    def _l10n_de_datev_get_csv(self, options, moves):
        date_from = fields.Date.from_string(options.get("date").get("date_from"))
        date_to = fields.Date.from_string(options.get("date").get("date_to"))
        fy = self.env.company.compute_fiscalyear_dates(date_to)

        date_from = datetime.strftime(date_from, "%Y%m%d")
        date_to = datetime.strftime(date_to, "%Y%m%d")
        fy = datetime.strftime(fy.get("date_from"), "%Y%m%d")
        datev_info = self._l10n_de_datev_get_client_number()
        account_length = self._l10n_de_datev_get_account_length()

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";", quotechar='"', quoting=2)

        preheader = [
            "EXTF", 700, 21, "Buchungsstapel", 13, "", "", "", "", "",
            datev_info[0], datev_info[1], fy, account_length, date_from,
            date_to, "", "", "", "", 0, "EUR", "", "", "", "", "", "", "", "",
        ]

        header = [
            "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz", "Kurs",
            "Basis-Umsatz", "WKZ Basis-Umsatz", "Konto", "Gegenkonto (ohne BU-Schlüssel)",
            "BU-Schlüssel", "Belegdatum", "Belegfeld 1", "Belegfeld 2", "Skonto", "Buchungstext",
            "Postensperre", "Diverse Adressnummer", "Geschäftspartnerbank", "Sachverhalt", "Zinssperre",
            "Beleglink", "Beleginfo - Art 1", "Beleginfo - Inhalt 1", "Beleginfo - Art 2", "Beleginfo - Inhalt 2",
            "Beleginfo - Art 3", "Beleginfo - Inhalt 3", "Beleginfo - Art 4", "Beleginfo - Inhalt 4",
            "Beleginfo - Art 5", "Beleginfo - Inhalt 5", "Beleginfo - Art 6", "Beleginfo - Inhalt 6",
            "Beleginfo - Art 7", "Beleginfo - Inhalt 7", "Beleginfo - Art 8", "Beleginfo - Inhalt 8",
            "KOST1 - Kostenstelle", "KOST2 - Kostenstelle", "Kost-Menge", "EU-Land u. UStID (Bestimmung)",
            "EU-Steuersatz (Bestimmung)", "Abw. Versteuerungsart", "Sachverhalt L+L", "Funktionsergänzung L+L",
            "BU 49 Hauptfunktionstyp", "BU 49 Hauptfunktionsnummer", "BU 49 Funktionsergänzung",
            "Zusatzinformation - Art 1", "Zusatzinformation- Inhalt 1", "Zusatzinformation - Art 2",
            "Zusatzinformation- Inhalt 2", "Zusatzinformation - Art 3", "Zusatzinformation- Inhalt 3",
            "Zusatzinformation - Art 4", "Zusatzinformation- Inhalt 4", "Zusatzinformation - Art 5",
            "Zusatzinformation- Inhalt 5", "Zusatzinformation - Art 6", "Zusatzinformation- Inhalt 6",
            "Zusatzinformation - Art 7", "Zusatzinformation- Inhalt 7", "Zusatzinformation - Art 8",
            "Zusatzinformation- Inhalt 8", "Zusatzinformation - Art 9", "Zusatzinformation- Inhalt 9",
            "Zusatzinformation - Art 10", "Zusatzinformation- Inhalt 10", "Zusatzinformation - Art 11",
            "Zusatzinformation- Inhalt 11", "Zusatzinformation - Art 12", "Zusatzinformation- Inhalt 12",
            "Zusatzinformation - Art 13", "Zusatzinformation- Inhalt 13", "Zusatzinformation - Art 14",
            "Zusatzinformation- Inhalt 14", "Zusatzinformation - Art 15", "Zusatzinformation- Inhalt 15",
            "Zusatzinformation - Art 16", "Zusatzinformation- Inhalt 16", "Zusatzinformation - Art 17",
            "Zusatzinformation- Inhalt 17", "Zusatzinformation - Art 18", "Zusatzinformation- Inhalt 18",
            "Zusatzinformation - Art 19", "Zusatzinformation- Inhalt 19", "Zusatzinformation - Art 20",
            "Zusatzinformation- Inhalt 20", "Stück", "Gewicht", "Zahlweise", "Forderungsart",
            "Veranlagungsjahr", "Zugeordnete Fälligkeit", "Skontotyp", "Auftragsnummer", "Buchungstyp",
            "USt-Schlüssel (Anzahlungen)", "EU-Land (Anzahlungen)", "Sachverhalt L+L (Anzahlungen)",
            "EU-Steuersatz (Anzahlungen)", "Erlöskonto (Anzahlungen)", "Herkunft-Kz", "Buchungs GUID",
            "KOST-Datum", "SEPA-Mandatsreferenz", "Skontosperre", "Gesellschaftername", "Beteiligtennummer",
            "Identifikationsnummer", "Zeichnernummer", "Postensperre bis", "Bezeichnung SoBil-Sachverhalt",
            "Kennzeichen SoBil-Buchung", "Festschreibung", "Leistungsdatum", "Datum Zuord. Steuerperiode",
            "Fälligkeit", "Generalumkehr (GU)", "Steuersatz", "Land", "Abrechnungsreferenz", "BVV-Position",
            "EU-Land u. UStID (Ursprung)", "EU-Steuersatz (Ursprung)", "Abw. Skontokonto",
        ]

        lines = [preheader, header]

        for m in moves:
            delta_by_aml = defaultdict(float)
            payment_account = 0
            move_balance = 0
            counterpart_amount = 0
            last_tax_line_index = 0

            def _get_code_correction(taxes):
                codes = set(taxes.mapped("l10n_de_datev_code"))
                return len(codes) == 1 and codes.pop() or ""

            for aml in m.line_ids:
                code_correction = ""

                if aml.debit == aml.credit:
                    continue

                to_account_code = str(
                    self._l10n_de_datev_find_partner_account(
                        aml.move_id.l10n_de_datev_main_account_id,
                        aml.partner_id,
                    )
                )
                account_code = u"{code}".format(
                    code=self._l10n_de_datev_find_partner_account(
                        aml.account_id,
                        aml.partner_id,
                    )
                )

                if aml.payment_id:
                    if not code_correction:
                        code_correction = _get_code_correction(m.line_ids.tax_ids)
                    if payment_account == 0:
                        payment_account = account_code
                        counterpart_amount += aml.balance
                        continue
                    to_account_code = payment_account

                if aml.account_id == aml.move_id.l10n_de_datev_main_account_id:
                    if aml.statement_line_id and not aml.payment_id:
                        counterpart_amount += aml.balance
                    continue

                if aml.tax_line_id:
                    continue

                if aml.price_total and m.move_type != "entry":
                    sign = -1 if aml.currency_id.compare_amounts(aml.balance, 0) < 0 else 1
                    line_amount_currency = abs(aml.price_total) * sign
                else:
                    aml_taxes = aml.tax_ids.compute_all(
                        aml.amount_currency,
                        aml.currency_id,
                        partner=aml.partner_id,
                        handle_price_include=False,
                    )
                    line_amount_currency = aml_taxes["total_included"]

                if aml.currency_id != aml.company_id.currency_id:
                    if not aml.currency_id.is_zero(line_amount_currency):
                        rate = m._get_product_base_line_currency_rate(aml)
                        line_amount = line_amount_currency / rate
                    else:
                        line_amount = aml.balance
                else:
                    line_amount = line_amount_currency

                move_balance += line_amount

                if aml.tax_ids:
                    last_tax_line_index = len(lines)
                    last_tax_line_amount = line_amount
                    code_correction = _get_code_correction(aml.tax_ids)
                elif (
                    aml.move_id.deferred_entry_type == "revenue"
                    and aml.move_id.deferred_original_move_ids
                    and (aml.account_id.code == "3900" or to_account_code == "3900")
                ):
                    code_correction = "40"

                receipt1 = ref = aml.move_id.name
                if aml.move_id.journal_id.type == "purchase" and aml.move_id.ref:
                    ref = aml.move_id.ref

                receipt2 = ""
                if to_account_code == account_code and aml.date_maturity:
                    receipt2 = aml.date

                array = ["" for x in range(125)]
                array[1] = "H" if aml.currency_id.compare_amounts(line_amount, 0) < 0 else "S"
                line_amount = abs(line_amount)
                line_amount_currency = abs(line_amount_currency) + delta_by_aml[aml]
                array[0] = float_repr(
                    line_amount_currency,
                    aml.currency_id.decimal_places,
                ).replace(".", ",")
                array[2] = aml.currency_id.name

                if aml.currency_id != aml.company_id.currency_id:
                    if not aml.company_id.currency_id.is_zero(line_amount) and not aml.currency_id.is_zero(line_amount_currency):
                        rate = round(line_amount_currency / line_amount, 6) or 1.0
                    else:
                        rate = 1.0
                    array[3] = str(rate).replace(".", ",")
                    array[4] = float_repr(
                        line_amount,
                        aml.company_id.currency_id.decimal_places,
                    ).replace(".", ",")
                    array[5] = aml.company_id.currency_id.name

                array[6] = account_code
                array[7] = to_account_code
                array[8] = code_correction
                array[9] = datetime.strftime(aml.move_id.date, "%-d%m")
                array[10] = receipt1[-36:]
                array[11] = receipt2
                array[13] = (aml.name or ref).replace("\n", " ")

                if m.message_main_attachment_id:
                    array[19] = f'BEDI "{m._l10n_de_datev_get_guid()}"'

                lines.append(array)

            if (
                (m.origin_payment_id or m.statement_line_id)
                and move_balance
                and counterpart_amount
                and last_tax_line_index
            ):
                delta_balance = move_balance + counterpart_amount
                if delta_balance:
                    lines[last_tax_line_index][0] = float_repr(
                        abs(last_tax_line_amount - delta_balance),
                        m.company_id.currency_id.decimal_places,
                    ).replace(".", ",")

        writer.writerows(lines)
        return output.getvalue()
