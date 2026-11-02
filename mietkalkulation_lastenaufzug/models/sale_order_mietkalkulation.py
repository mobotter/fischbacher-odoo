# -*- coding: utf-8 -*-

import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    _MK_LKW_STUNDENSATZ = 140.0
    _MK_DEMONTAGE_FAKTOR = 0.80
    _MK_BAUSTELLENBESICHTIGUNG_PREIS = 150.0
    _MK_WARTUNG_PREIS_4_WOCHEN = 140.0

    _MK_BUEHNENGROESSE_PREISMODELL_NAMEN = {
        'GEDA 1200 Z/ZP',
        'GEDA 1500 Z/ZP',
    }

    _MK_KEINE_PERSONENBEFOERDERUNG_PREISMODELL_NAMEN = {
        'GEDA 200 Z',
        'GEDA 300 Z',
        'GEDA 500 Z',
    }

    # ── Standardwerte und Hilfsmethoden ───────────────────────────────────────

    def _default_mk_preistabelle_id(self):
        preismodell = self.env.ref(
            'mietkalkulation_lastenaufzug.mk_preis_500',
            raise_if_not_found=False,
        )

        if not preismodell:
            preismodell = self.env['mk.preistabelle'].search(
                [
                    ('name', '=', '500 Z/ZP'),
                    ('active', '=', True),
                ],
                limit=1,
            )

        if not preismodell:
            preismodell = self.env['mk.preistabelle'].browse(921).exists()

        return preismodell

    @staticmethod
    def _round_up_to_1(amount):
        """Rundet positive Beträge auf den nächsten vollen Euro auf."""
        if amount <= 0.0:
            return 0.0

        return float(math.ceil(amount - 1e-9))

    def _get_rabattsatz(self, monate):
        """Liefert den Rabattfaktor, zum Beispiel 0.05 für 5 Prozent."""
        staffeln = self.env['mk.rabattstaffel'].search(
            [('active', '=', True)],
            order='monate_ab desc',
        )

        for staffel in staffeln:
            if monate >= staffel.monate_ab:
                return (staffel.rabatt_prozent or 0.0) / 100.0

        return 0.0

    @staticmethod
    def _format_mk_number(value, digits=2):
        """Formatiert eine Zahl deutsch, zum Beispiel 20,00."""
        return format(value or 0.0, f'.{digits}f').replace('.', ',')

    @classmethod
    def _is_mk_buehnengroesse_preismodell(cls, preismodell):
        """Prüft, ob das Preismodell eine auswählbare Bühnenoption hat."""
        return bool(
            preismodell
            and preismodell.name in cls._MK_BUEHNENGROESSE_PREISMODELL_NAMEN
        )

    @classmethod
    def _is_mk_personenbefoerderung_preismodell(cls, preismodell):
        """
        Prüft, ob Personenbeförderung für das Preismodell berechnet wird.

        Bei GEDA 200 Z, GEDA 300 Z und GEDA 500 Z wird kein Mehrpreis
        für Personenbeförderung angesetzt. Bei allen anderen Modellen
        wird der im Preismodell hinterlegte Mehrpreis automatisch
        angesetzt.
        """
        return bool(
            preismodell
            and preismodell.name
            not in cls._MK_KEINE_PERSONENBEFOERDERUNG_PREISMODELL_NAMEN
        )

    # ── Eingaben ──────────────────────────────────────────────────────────────

    mk_preistabelle_id = fields.Many2one(
        comodel_name='mk.preistabelle',
        string='Aufzug / Preismodell',
        domain=[
            ('active', '=', True),
        ],
        default=_default_mk_preistabelle_id,
        ondelete='restrict',
        help='Preiszeile für die Mietkalkulation auswählen.',
    )

    mk_aufbauhoehe = fields.Float(
        string='Aufbauhöhe gesamt (m)',
        default=20.0,
    )

    mk_buehnengroesse = fields.Selection(
        selection=[
            ('keine', 'Keine'),
            ('145x325', 'Lastbühne 1,45 × 3,25 m'),
            ('165x435', 'Lastbühne 1,65 × 4,35 m'),
        ],
        string='Bühnengröße',
        default='keine',
    )

    mk_buehnengroesse_sichtbar = fields.Boolean(
        string='Bühnengröße anzeigen',
        compute='_compute_mk_preismodell_sichtbarkeiten',
        store=False,
    )

    mk_personenbefoerderung_sichtbar = fields.Boolean(
        string='Personenbeförderung anzeigen',
        compute='_compute_mk_preismodell_sichtbarkeiten',
        store=False,
    )

    mk_extra_stationen = fields.Integer(
        string='Zusätzliche Be-/Entladestellen',
        default=0,
        help=(
            'EG und 1. OG sind im Grundpreis enthalten. '
            'Hier nur weitere Be-/Entladestellen eintragen.'
        ),
    )

    mk_mietdauer_wochen = fields.Integer(
        string='Mietdauer (Wochen)',
        default=16,
    )

    mk_transport_stunden = fields.Float(
        string='Transport LKW (Stunden)',
        default=2.0,
    )

    mk_mit_transport = fields.Boolean(
        string='Mit Transport',
        default=False,
        help='Wenn deaktiviert, werden keine LKW-Transportkosten berechnet.',
    )

    mk_wartung_inklusive = fields.Boolean(
        string='Wartung inklusive',
        default=False,
        help=(
            'Bei Aktivierung wird die turnusmäßige Wartung inklusive '
            'erforderlicher Schmiermittel alle vier Wochen berechnet.'
        ),
    )

    mk_baustromanschluss = fields.Selection(
        selection=[
            ('230_400v', '230/400 V'),
            ('5_16a', '5/16 A'),
            ('5_32a', '5/32 A'),
            ('63a', '63 A'),
        ],
        string='Baustromanschluss',
        help='Erforderlicher bauseitiger Baustromanschluss.',
    )

    mk_montageart = fields.Selection(
        selection=[
            ('geruest', 'Am Gerüst'),
            ('gebaeude', 'Am Gebäude'),
            ('selbstmontage', 'Selbstmontage / Bausatz'),
        ],
        string='Montage',
        required=True,
        default='selbstmontage',
        help='Bestimmt den Faktor für die kalkulierten Montagestunden.',
    )

    mk_rabatt_manuell = fields.Boolean(
        string='Rabatt manuell festlegen',
        default=False,
        help=(
            'Wenn aktiv, wird der manuell eingegebene Rabatt '
            'statt der Rabattstaffel verwendet.'
        ),
    )

    mk_rabatt_prozent_override = fields.Float(
        string='Rabatt manuell (%)',
        digits=(16, 2),
        default=0.0,
        help='Manueller Rabatt zwischen 0,00 % und 100,00 %.',
    )

    # ── Montage-Einstellwerte ─────────────────────────────────────────────────

    mk_monteur_stundensatz = fields.Float(
        string='Monteur Stundensatz (€)',
        default=98.0,
    )

    mk_mit_helfer = fields.Boolean(
        string='Mit Helfer',
        default=True,
        help=(
            'Wenn deaktiviert, wird kein Helfer kalkuliert. '
            'Der Helfer-Stundensatz wird dann nicht in den '
            'Montagepreis einbezogen.'
        ),
    )

    mk_helfer_stundensatz = fields.Float(
        string='Helfer Stundensatz (€)',
        default=55.0,
    )

    mk_std_je_station = fields.Float(
        string='Stunden je Be-/Entladestelle',
        default=1.0,
    )

    mk_faktor_geruest = fields.Float(
        string='Faktor Gerüst',
        default=1.0,
    )

    mk_faktor_gebaeude = fields.Float(
        string='Faktor Gebäude',
        default=1.25,
    )

    # ── Preislistenanzeige ────────────────────────────────────────────────────

    mk_preistabelle_ids = fields.Many2many(
        comodel_name='mk.preistabelle',
        string='Mietpreistabelle',
        relation='sale_order_mk_preistabelle_rel',
        column1='order_id',
        column2='preistabelle_id',
    )

    # ── Berechnungsfelder: Mietpreis ──────────────────────────────────────────

    mk_grundpreis = fields.Float(
        string='Grundpreis bis 15 m (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_extra_hoehenabschnitte = fields.Integer(
        string='Zusätzl. Höhenabschnitte à 1,5 m',
        compute='_compute_mk',
        store=True,
    )

    mk_mehrpreis_hoehe = fields.Float(
        string='Mehrpreis Höhe (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_mehrpreis_stationen = fields.Float(
        string='Mehrpreis Be-/Entladestellen (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_mehrpreis_buehne = fields.Float(
        string='Mehrpreis Bühne (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_mehrpreis_person = fields.Float(
        string='Mehrpreis Personenbeförderung (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_zwischensumme = fields.Float(
        string='Zwischensumme pro 4 Wochen (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_rabatt_prozent = fields.Float(
        string='Rabatt angewendet (%)',
        compute='_compute_mk',
        store=True,
        digits=(16, 2),
        readonly=True,
    )

    mk_preis_nach_rabatt_roh = fields.Float(
        string='Preis nach Rabatt ungerundet (€)',
        compute='_compute_mk',
        store=True,
        digits=(16, 2),
    )

    mk_preis_nach_rabatt = fields.Float(
        string='Preis nach Rabatt (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_preis_verlaengerungswoche_roh = fields.Float(
        string='Preis Verlängerungswoche ungerundet (€)',
        compute='_compute_mk',
        store=True,
        digits=(16, 2),
    )

    mk_preis_verlaengerungswoche = fields.Float(
        string='Preis Verlängerungswoche (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_maschinenbruch_roh = fields.Float(
        string='Maschinenbruchversicherung ungerundet (€)',
        compute='_compute_mk',
        store=True,
        digits=(16, 2),
    )

    mk_maschinenbruch = fields.Float(
        string='Maschinenbruchversicherung 4% (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_gesamt_4wochen = fields.Float(
        string='Gesamt pro 4 Wochen (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_gesamt_mietdauer = fields.Float(
        string='Gesamtpreis für komplette Mietdauer (€)',
        compute='_compute_mk',
        store=True,
    )

    # ── Berechnungsfelder: Montage, Demontage und Transport ───────────────────

    mk_stunden_aufbau = fields.Float(
        string='Montagestunden Aufbauhöhe',
        compute='_compute_mk',
        store=True,
    )

    mk_stunden_stationen = fields.Float(
        string='Montagestunden Stationen',
        compute='_compute_mk',
        store=True,
    )

    mk_gesamtstunden = fields.Float(
        string='Gesamtstunden Team Montage',
        compute='_compute_mk',
        store=True,
    )

    mk_demontage_stunden = fields.Float(
        string='Gesamtstunden Team Demontage',
        compute='_compute_mk',
        store=True,
        help=(
            'Kalkulierte Demontagezeit: 80 % der '
            'kalkulierten Montagestunden.'
        ),
    )

    mk_team_kosten_stunde = fields.Float(
        string='Teamkosten pro Stunde (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_montage_geruest = fields.Float(
        string='Montagekosten am Gerüst (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_montage_gebaeude = fields.Float(
        string='Montagekosten am Gebäude (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_transportkosten_lkw = fields.Float(
        string='Transportkosten LKW (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_montage_gesamt_geruest = fields.Float(
        string='Montage inkl. Transport am Gerüst (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_montage_gesamt_gebaeude = fields.Float(
        string='Montage inkl. Transport am Gebäude (€)',
        compute='_compute_mk',
        store=True,
    )

    mk_montage_gesamt = fields.Float(
        string='Gesamtpreis für Montage (€)',
        compute='_compute_mk',
        store=True,
        help=(
            'Finaler Montagepreis entsprechend der ausgewählten '
            'Montageart, ohne Transportkosten.'
        ),
    )

    mk_demontage_kosten = fields.Float(
        string='Gesamtpreis für Demontage (€)',
        compute='_compute_mk',
        store=True,
        help=(
            'Kalkulierte Demontagekosten: 80 % der '
            'kalkulierten Montagekosten, ohne Transportkosten.'
        ),
    )

    # ── Sichtbarkeiten und Onchange ───────────────────────────────────────────

    @api.depends('mk_preistabelle_id', 'mk_preistabelle_id.name')
    def _compute_mk_preismodell_sichtbarkeiten(self):
        for rec in self:
            preismodell = rec.mk_preistabelle_id

            rec.mk_buehnengroesse_sichtbar = (
                rec._is_mk_buehnengroesse_preismodell(preismodell)
            )
            rec.mk_personenbefoerderung_sichtbar = (
                rec._is_mk_personenbefoerderung_preismodell(preismodell)
            )

    @api.onchange('mk_preistabelle_id')
    def _onchange_mk_preistabelle_id_reset_buehnengroesse(self):
        for rec in self:
            if not rec._is_mk_buehnengroesse_preismodell(
                rec.mk_preistabelle_id
            ):
                rec.mk_buehnengroesse = 'keine'

    # ── Mietkalkulation ───────────────────────────────────────────────────────

    @api.depends(
        'mk_preistabelle_id',
        'mk_preistabelle_id.name',
        'mk_preistabelle_id.grundpreis',
        'mk_preistabelle_id.mehrpreis_hoehe',
        'mk_preistabelle_id.mehrpreis_station',
        'mk_preistabelle_id.mehrpreis_buehne_145',
        'mk_preistabelle_id.mehrpreis_buehne_165',
        'mk_preistabelle_id.mehrpreis_person',
        'mk_preistabelle_id.std_je_5m',
        'mk_aufbauhoehe',
        'mk_buehnengroesse',
        'mk_extra_stationen',
        'mk_mietdauer_wochen',
        'mk_rabatt_manuell',
        'mk_rabatt_prozent_override',
        'mk_transport_stunden',
        'mk_mit_transport',
        'mk_montageart',
        'mk_monteur_stundensatz',
        'mk_mit_helfer',
        'mk_helfer_stundensatz',
        'mk_std_je_station',
        'mk_faktor_geruest',
        'mk_faktor_gebaeude',
    )
    def _compute_mk(self):
        config = self.env['ir.config_parameter'].sudo()

        def get_float_param(key, default):
            value = config.get_param(key, default)
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        basis_hoehe = get_float_param(
            'mietkalkulation_lastenaufzug.basis_hoehe_grundgeraet',
            15.0,
        )
        schrittweite = get_float_param(
            'mietkalkulation_lastenaufzug.schrittweite_mehrhoehe',
            1.5,
        )
        maschinenbruch_prozent = get_float_param(
            'mietkalkulation_lastenaufzug.maschinenbruch_prozent',
            4.0,
        )

        if schrittweite <= 0.0:
            schrittweite = 1.5

        for rec in self:
            preismodell = rec.mk_preistabelle_id
            buehnengroesse_erlaubt = (
                rec._is_mk_buehnengroesse_preismodell(preismodell)
            )
            personenbefoerderung_erlaubt = (
                rec._is_mk_personenbefoerderung_preismodell(preismodell)
            )

            grundpreis = preismodell.grundpreis if preismodell else 0.0
            mehrpreis_hoehe = (
                preismodell.mehrpreis_hoehe if preismodell else 0.0
            )
            mehrpreis_station = (
                preismodell.mehrpreis_station if preismodell else 0.0
            )
            mehrpreis_buehne_145 = (
                preismodell.mehrpreis_buehne_145
                if preismodell
                else 0.0
            )
            mehrpreis_buehne_165 = (
                preismodell.mehrpreis_buehne_165
                if preismodell
                else 0.0
            )
            mehrpreis_person = (
                preismodell.mehrpreis_person if preismodell else 0.0
            )
            std_je_5m = preismodell.std_je_5m if preismodell else 1.8

            rec.mk_grundpreis = grundpreis

            extra_abschnitte = max(
                0,
                math.ceil(
                    (max(rec.mk_aufbauhoehe, 0.0) - basis_hoehe)
                    / schrittweite
                ),
            )
            rec.mk_extra_hoehenabschnitte = extra_abschnitte

            rec.mk_mehrpreis_hoehe = (
                extra_abschnitte * mehrpreis_hoehe
            )
            rec.mk_mehrpreis_stationen = (
                max(rec.mk_extra_stationen, 0) * mehrpreis_station
            )

            if (
                buehnengroesse_erlaubt
                and rec.mk_buehnengroesse == '145x325'
            ):
                rec.mk_mehrpreis_buehne = mehrpreis_buehne_145
            elif (
                buehnengroesse_erlaubt
                and rec.mk_buehnengroesse == '165x435'
            ):
                rec.mk_mehrpreis_buehne = mehrpreis_buehne_165
            else:
                rec.mk_mehrpreis_buehne = 0.0

            rec.mk_mehrpreis_person = (
                mehrpreis_person
                if personenbefoerderung_erlaubt
                else 0.0
            )

            zwischensumme = (
                rec.mk_grundpreis
                + rec.mk_mehrpreis_hoehe
                + rec.mk_mehrpreis_stationen
                + rec.mk_mehrpreis_buehne
                + rec.mk_mehrpreis_person
            )
            rec.mk_zwischensumme = zwischensumme

            monate = max(rec.mk_mietdauer_wochen, 0) / 4.0
            rabatt_prozent = (
                rec.mk_rabatt_prozent_override
                if rec.mk_rabatt_manuell
                else rec._get_rabattsatz(monate) * 100.0
            )
            rabatt_prozent = max(0.0, min(rabatt_prozent, 100.0))
            rec.mk_rabatt_prozent = rabatt_prozent

            preis_nach_rabatt_roh = zwischensumme * (
                1.0 - rabatt_prozent / 100.0
            )
            rec.mk_preis_nach_rabatt_roh = preis_nach_rabatt_roh

            preis_verlaengerungswoche_roh = preis_nach_rabatt_roh / 4.0
            rec.mk_preis_verlaengerungswoche_roh = (
                preis_verlaengerungswoche_roh
            )

            preis_verlaengerungswoche = rec._round_up_to_1(
                preis_verlaengerungswoche_roh
            )
            rec.mk_preis_verlaengerungswoche = (
                preis_verlaengerungswoche
            )

            preis_nach_rabatt = preis_verlaengerungswoche * 4.0
            rec.mk_preis_nach_rabatt = preis_nach_rabatt

            maschinenbruch_roh = (
                preis_nach_rabatt
                * (maschinenbruch_prozent / 100.0)
            )
            rec.mk_maschinenbruch_roh = maschinenbruch_roh
            rec.mk_maschinenbruch = rec._round_up_to_1(
                maschinenbruch_roh
            )

            gesamt_4wochen = preis_nach_rabatt + rec.mk_maschinenbruch
            rec.mk_gesamt_4wochen = gesamt_4wochen
            rec.mk_gesamt_mietdauer = (
                gesamt_4wochen
                * (max(rec.mk_mietdauer_wochen, 0) / 4.0)
            )

            stunden_aufbau_basis = (
                max(rec.mk_aufbauhoehe, 0.0) / 5.0
            ) * std_je_5m

            stunden_stationen_basis = (
                1 + max(rec.mk_extra_stationen, 0)
            ) * rec.mk_std_je_station

            gesamtstunden_basis = (
                stunden_aufbau_basis + stunden_stationen_basis
            )

            helfer_stundensatz = (
                rec.mk_helfer_stundensatz
                if rec.mk_mit_helfer
                else 0.0
            )
            team_kosten_stunde = (
                rec.mk_monteur_stundensatz + helfer_stundensatz
            )
            rec.mk_team_kosten_stunde = team_kosten_stunde

            montage_geruest = (
                gesamtstunden_basis
                * team_kosten_stunde
                * rec.mk_faktor_geruest
            )
            montage_gebaeude = (
                gesamtstunden_basis
                * team_kosten_stunde
                * rec.mk_faktor_gebaeude
            )
            rec.mk_montage_geruest = montage_geruest
            rec.mk_montage_gebaeude = montage_gebaeude

            if rec.mk_montageart == 'gebaeude':
                montage_faktor = rec.mk_faktor_gebaeude
                montage_ohne_transport = montage_gebaeude
            elif rec.mk_montageart == 'selbstmontage':
                montage_faktor = 0.0
                montage_ohne_transport = 0.0
            else:
                montage_faktor = rec.mk_faktor_geruest
                montage_ohne_transport = montage_geruest

            rec.mk_stunden_aufbau = (
                stunden_aufbau_basis * montage_faktor
            )
            rec.mk_stunden_stationen = (
                stunden_stationen_basis * montage_faktor
            )
            rec.mk_gesamtstunden = (
                gesamtstunden_basis * montage_faktor
            )
            rec.mk_demontage_stunden = (
                rec.mk_gesamtstunden * self._MK_DEMONTAGE_FAKTOR
            )
            rec.mk_demontage_kosten = (
                montage_ohne_transport * self._MK_DEMONTAGE_FAKTOR
            )

            transportkosten = (
                max(rec.mk_transport_stunden, 0.0)
                * self._MK_LKW_STUNDENSATZ
                if rec.mk_mit_transport
                else 0.0
            )
            rec.mk_transportkosten_lkw = transportkosten

            rec.mk_montage_gesamt_geruest = (
                montage_geruest + transportkosten
            )
            rec.mk_montage_gesamt_gebaeude = (
                montage_gebaeude + transportkosten
            )
            rec.mk_montage_gesamt = montage_ohne_transport

    # ── Angebotspositionen aus Mietkalkulation ────────────────────────────────

    def action_generate_mk_quotation_lines(self):
        """Erzeugt bzw. ersetzt Angebotspositionen aus der Mietkalkulation."""
        self.ensure_one()

        if not self.id:
            raise UserError(
                _(
                    'Bitte speichern Sie das Angebot zuerst, bevor '
                    'Sie Angebotszeilen generieren.'
                )
            )

        required_order_fields = {
            'quotation_line_ids',
            'offer_intro_text',
        }
        missing_order_fields = required_order_fields - set(self._fields)

        if missing_order_fields:
            raise UserError(
                _(
                    'Im Angebot fehlen folgende Felder: %(fields)s. '
                    'Bitte prüfen Sie, ob das Modul '
                    '„ol_sale_subscription_extensions“ installiert '
                    'und aktualisiert ist.'
                ) % {
                    'fields': ', '.join(sorted(missing_order_fields)),
                }
            )

        if not self.mk_preistabelle_id:
            raise UserError(
                _(
                    'Bitte wählen Sie zuerst ein Aufzug- bzw. '
                    'Preismodell aus.'
                )
            )

        quotation_line_model = self.env['sale.quotation.line']

        required_line_fields = {
            'is_mk_generated',
            'quotation_product_name',
            'product_uom_qty',
            'product_uom',
            'price_unit',
            'discount',
            'price_subtotal',
        }
        missing_line_fields = required_line_fields - set(
            quotation_line_model._fields
        )

        if missing_line_fields:
            raise UserError(
                _(
                    'Im Modell „sale.quotation.line“ fehlen folgende '
                    'Felder: %(fields)s. Bitte aktualisieren Sie das '
                    'Modul „ol_sale_subscription_extensions“.'
                ) % {
                    'fields': ', '.join(sorted(missing_line_fields)),
                }
            )

        self.quotation_line_ids.filtered(
            lambda line: line.is_mk_generated
        ).unlink()

        unit_uom = self.env.ref(
            'uom.product_uom_unit',
            raise_if_not_found=False,
        )
        week_uom = self.env.ref(
            'uom.product_uom_week',
            raise_if_not_found=False,
        )
        hour_uom = self.env['uom.uom'].search(
            [
                (
                    'name',
                    'in',
                    ['Hour(s)', 'Hour', 'Stunde(n)', 'Stunde', 'h'],
                ),
            ],
            limit=1,
        )

        unit_uom_id = unit_uom.id if unit_uom else False
        week_uom_id = week_uom.id if week_uom else unit_uom_id
        hour_uom_id = hour_uom.id if hour_uom else unit_uom_id

        be_entladestellen = (
            max(int(self.mk_extra_stationen or 0), 0) + 1
        )

        preismodell_name = (
            self.mk_preistabelle_id.display_name
            or self.mk_preistabelle_id.name
            or ''
        ).strip()

        offer_intro_text = _(
            'Sehr geehrte Damen und Herren,\n\n'
            'vielen Dank für Ihr Interesse am Aufzug '
            '%(preismodell)s für %(wochen)d Wochen. '
            'Anbei erhalten Sie unser Angebot.\n\n'
            'Bei Fragen stehen wir Ihnen gerne zur Verfügung.'
        ) % {
            'preismodell': preismodell_name,
            'wochen': max(int(self.mk_mietdauer_wochen or 0), 0),
        }

        preismodell_beschreibung = (
            self.mk_preistabelle_id.beschreibung or ''
        ).strip()

        description_parts = [
            _('Lastenaufzug: %(preismodell)s') % {
                'preismodell': preismodell_name,
            },
        ]

        if preismodell_beschreibung:
            description_parts.append(preismodell_beschreibung)

        if (
            self.mk_buehnengroesse_sichtbar
            and self.mk_buehnengroesse
            and self.mk_buehnengroesse != 'keine'
        ):
            buehnenbezeichnungen = dict(
                self._fields['mk_buehnengroesse'].selection
            )
            buehnengroesse = buehnenbezeichnungen.get(
                self.mk_buehnengroesse,
                self.mk_buehnengroesse,
            )
            description_parts.append(
                _('Bühne %(buehne)s') % {
                    'buehne': buehnengroesse,
                }
            )

        description_parts.extend([
            _('Nutzhöhe ca. %(aufbauhoehe)s m') % {
                'aufbauhoehe': self._format_mk_number(
                    self.mk_aufbauhoehe
                ),
            },
            _('%(stationen)d Haltestellen') % {
                'stationen': be_entladestellen,
            },
        ])

        is_selbstmontage = self.mk_montageart == 'selbstmontage'

        baustellenbesichtigung_preis = 0.0
        montage_stunden = 0.0
        demontage_stunden = 0.0
        montage_preis = 0.0
        demontage_preis = 0.0

        if is_selbstmontage:
            baustellenbesichtigung_text = _(
                'Baustellenbesichtigung'
            )
            montage_text = _('Montage bauseits')
            demontage_text = _('Demontage bauseits')

        elif self.mk_mit_helfer:
            baustellenbesichtigung_text = _(
                'durch Monteur und Helfer'
            )
            baustellenbesichtigung_preis = (
                self._MK_BAUSTELLENBESICHTIGUNG_PREIS
            )
            montage_text = _(
                'Montage durch Monteur und Helfer'
            )
            demontage_text = _(
                'Demontage durch Monteur und Helfer'
            )
            montage_stunden = max(self.mk_gesamtstunden or 0.0, 0.0)
            demontage_stunden = max(
                self.mk_demontage_stunden or 0.0,
                0.0,
            )
            montage_preis = max(
                self.mk_team_kosten_stunde or 0.0,
                0.0,
            )
            demontage_preis = montage_preis

        else:
            baustellenbesichtigung_text = _(
                'Besichtigung durch Monteur, Helfer bauseits'
            )
            baustellenbesichtigung_preis = (
                self._MK_BAUSTELLENBESICHTIGUNG_PREIS
            )
            montage_text = _(
                'Montage durch Monteur, Helfer bauseits'
            )
            demontage_text = _(
                'Demontage durch Monteur, Helfer bauseits'
            )
            montage_stunden = max(self.mk_gesamtstunden or 0.0, 0.0)
            demontage_stunden = max(
                self.mk_demontage_stunden or 0.0,
                0.0,
            )
            montage_preis = max(
                self.mk_team_kosten_stunde or 0.0,
                0.0,
            )
            demontage_preis = montage_preis

        transport_name = (
            _('mit LKW')
            if self.mk_mit_transport
            else _('Transport bauseits')
        )
        transport_menge = (
            max(self.mk_transport_stunden or 0.0, 0.0)
            if self.mk_mit_transport
            else 1.0
        )
        transport_preis = (
            self._MK_LKW_STUNDENSATZ
            if self.mk_mit_transport
            else 0.0
        )

        baustromanschluss_auswahl = dict(
            self._fields['mk_baustromanschluss'].selection
        )
        baustromanschluss = baustromanschluss_auswahl.get(
            self.mk_baustromanschluss,
            False,
        )

        zusatzbedingungen_parts = []

        if is_selbstmontage:
            zusatzbedingungen_parts.append(
                _('Angebot wurde ohne Baustellenbesichtigung erstellt.')
            )
        else:
            zusatzbedingungen_parts.append(
                _(
                    'Kalkulierte Montagezeit ca. %(stunden)s Std. '
                    'pro Monteur – Mehrkosten werden gesondert '
                    'berechnet.'
                ) % {
                    'stunden': self._format_mk_number(
                        self.mk_gesamtstunden
                    ),
                }
            )

        if not is_selbstmontage and not self.mk_mit_helfer:
            zusatzbedingungen_parts.append(
                _(
                    'Bei der Montage und Demontage gehen wir von der '
                    'Gestellung eines Helfers bauseits aus.'
                )
            )

        if self.mk_wartung_inklusive:
            zusatzbedingungen_parts.append(
                _(
                    'Wartung 1x monatlich inklusive erforderlicher '
                    'Schmiermittel – turnusmäßig alle 4 Wochen/PA '
                    '(EUR 140,00).'
                )
            )
        else:
            zusatzbedingungen_parts.append(
                _(
                    'Notwendige Wartungs- und Schmierarbeiten wie '
                    'Sachkundigenprüfung, ZÜS etc. sind im Mietpreis '
                    'nicht enthalten.'
                )
            )

        if baustromanschluss:
            zusatzbedingungen_parts.append(
                _(
                    'Erforderlicher Baustromanschluss bauseits: '
                    '%(anschluss)s.'
                ) % {
                    'anschluss': baustromanschluss,
                }
            )

        zusatzbedingungen_text = '\n'.join(zusatzbedingungen_parts)

        wartung_name = (
            _(
                'Wartung 1x monatlich inkl. erforderlicher '
                'Schmiermittel'
            )
            if self.mk_wartung_inklusive
            else _('Wartung')
        )
        wartung_text = (
            _('Turnusmäßig alle 4 Wochen/PA.')
            if self.mk_wartung_inklusive
            else _(
                'Notwendige Wartungs- und Schmierarbeiten sind im '
                'Mietpreis nicht enthalten.'
            )
        )
        wartung_preis = (
            self._MK_WARTUNG_PREIS_4_WOCHEN
            if self.mk_wartung_inklusive
            else 0.0
        )

        lines_to_create = [
            {
                'order_id': self.id,
                'sequence': 9000,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _('Mietpreis / 4 Wochen'),
                'name': '\n'.join(description_parts),
                'product_uom_qty': 1.0,
                'product_uom': unit_uom_id,
                'price_unit': self.mk_gesamt_4wochen,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9010,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _(
                    'Mietpreis pro Verlängerungswoche'
                ),
                'name': _('von POS 1'),
                'product_uom_qty': 1.0,
                'product_uom': week_uom_id,
                'price_unit': self.mk_preis_verlaengerungswoche,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9020,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _(
                    'Baustellenbesichtigung'
                ),
                'name': baustellenbesichtigung_text,
                'product_uom_qty': 1.0,
                'product_uom': unit_uom_id,
                'price_unit': baustellenbesichtigung_preis,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9030,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _('Montage'),
                'name': montage_text,
                'product_uom_qty': (
                    1.0 if is_selbstmontage else montage_stunden
                ),
                'product_uom': hour_uom_id,
                'price_unit': montage_preis,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9040,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _('Demontage'),
                'name': demontage_text,
                'product_uom_qty': (
                    1.0 if is_selbstmontage else demontage_stunden
                ),
                'product_uom': hour_uom_id,
                'price_unit': demontage_preis,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9050,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _(
                    'Maschinenbruch-Versicherung'
                ),
                'name': _(
                    'Aufzug pro 4 Wochen mit EUR 1.360,00 '
                    'Selbstbehalt pro Schaden'
                ),
                'product_uom_qty': 1.0,
                'product_uom': week_uom_id,
                'price_unit': self.mk_maschinenbruch,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9060,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': wartung_name,
                'name': wartung_text,
                'product_uom_qty': 1.0,
                'product_uom': week_uom_id,
                'price_unit': wartung_preis,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9070,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _('Transport'),
                'name': transport_name,
                'product_uom_qty': transport_menge,
                'product_uom': hour_uom_id,
                'price_unit': transport_preis,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
            {
                'order_id': self.id,
                'sequence': 9080,
                'display_type': False,
                'is_mk_generated': True,
                'product_id': False,
                'quotation_product_name': _('Zusatzbedingungen'),
                'name': zusatzbedingungen_text,
                'product_uom_qty': 1.0,
                'product_uom': unit_uom_id,
                'price_unit': 0.0,
                'discount': 0.0,
                'tax_id': [(6, 0, [])],
            },
        ]

        self.write({
            'offer_intro_text': offer_intro_text,
        })

        created_lines = quotation_line_model.create(lines_to_create)

        if not created_lines:
            raise UserError(
                _('Es konnten keine Angebotspositionen erstellt werden.')
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # ── Standardwerte ─────────────────────────────────────────────────────────

    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if 'mk_preistabelle_ids' in fields_list:
            preise = self.env['mk.preistabelle'].search(
                [('active', '=', True)]
            )
            res['mk_preistabelle_ids'] = [
                fields.Command.set(preise.ids)
            ]

        return res
