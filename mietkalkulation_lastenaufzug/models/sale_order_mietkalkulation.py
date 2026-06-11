# -*- coding: utf-8 -*-
from odoo import api, fields, models
import math


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ─── Eingaben ────────────────────────────────────────────────────────────
    mk_traglast = fields.Selection([
        ('200', '200 kg'),
        ('300', '300 kg'),
        ('500', '500 kg'),
        ('1000', '1000 / 1200 kg'),
        ('1500', '1500 kg'),
        ('2000', '2000 kg'),
    ], string='Traglast (kg)', default='500')

    mk_aufbauhoehe = fields.Float(
        string='Aufbauhöhe gesamt (m)', default=20.0,
        help='Gesamte Aufbauhöhe des Lastenaufzugs in Metern'
    )

    mk_buehnengroesse = fields.Selection([
        ('keine', 'Keine'),
        ('145x325', 'Lastbühne 1,45 × 3,25 m'),
        ('165x435', 'Lastbühne 1,65 × 4,35 m'),
    ], string='Bühnengröße', default='keine')

    mk_personenbefoerderung = fields.Boolean(
        string='Personenbeförderung', default=False
    )

    mk_extra_stationen = fields.Integer(
        string='Zusätzliche Be-/Entladestellen\n(zusätzlich zu EG + OG)',
        default=0,
        help='Anzahl der zusätzlichen Haltestellen über EG und 1. OG hinaus'
    )

    mk_mietdauer_wochen = fields.Integer(
        string='Mietdauer (Wochen)', default=16,
        help='Mietdauer für Rabattberechnung (1 Monat = 4 Wochen)'
    )

    mk_transport_stunden = fields.Float(
        string='Transport in Stunden (LKW)', default=2.0
    )

    # Montage-Einstellwerte
    mk_monteur_stundensatz = fields.Float(
        string='Monteur Stundensatz (€)', default=88.0
    )
    mk_helfer_stundensatz = fields.Float(
        string='Helfer Stundensatz (€)', default=42.0
    )
    mk_std_je_station = fields.Float(
        string='Stunden je Be-/Entladestelle (Team)', default=1.0
    )
    mk_faktor_geruest = fields.Float(
        string='Faktor Gerüst', default=1.0
    )
    mk_faktor_gebaeude = fields.Float(
        string='Faktor Gebäude', default=1.25
    )

    # ─── Berechnungsfelder (readonly, compute) ────────────────────────────────
    mk_grundpreis = fields.Float(
        string='Grundpreis bis 15 m (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_extra_hoehenabschnitte = fields.Integer(
        string='Zusätzliche Höhenabschnitte à 1,5 m',
        compute='_compute_mietkalkulation', store=True
    )
    mk_mehrpreis_hoehe = fields.Float(
        string='Mehrpreis Höhe (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_mehrpreis_stationen = fields.Float(
        string='Mehrpreis zusätzl. Be-/Entladestellen (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_mehrpreis_buehne = fields.Float(
        string='Mehrpreis Bühne (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_mehrpreis_person = fields.Float(
        string='Mehrpreis Personenbeförderung (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_zwischensumme = fields.Float(
        string='Zwischensumme (pro 4 Wochen) (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_rabatt_prozent = fields.Float(
        string='Rabatt % (nach Mietdauer)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_preis_nach_rabatt = fields.Float(
        string='Preis nach Rabatt (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_preis_verlaengerungswoche = fields.Float(
        string='Preis Verlängerungswoche (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_maschinenbruch = fields.Float(
        string='Maschinenbruchversicherung 4% (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_gesamt_4wochen = fields.Float(
        string='Gesamt pro 4 Wochen (€)',
        compute='_compute_mietkalkulation', store=True
    )

    # Montage
    mk_stunden_aufbau = fields.Float(
        string='Stunden Aufbauhöhe',
        compute='_compute_mietkalkulation', store=True
    )
    mk_stunden_stationen = fields.Float(
        string='Stunden Stationen',
        compute='_compute_mietkalkulation', store=True
    )
    mk_gesamtstunden = fields.Float(
        string='Gesamtstunden (Team)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_team_kosten_stunde = fields.Float(
        string='Team-Kosten pro Stunde (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_montage_geruest = fields.Float(
        string='Montagekosten an Gerüst (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_montage_gebaeude = fields.Float(
        string='Montagekosten an Gebäude (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_transportkosten_lkw = fields.Float(
        string='Transportkosten LKW ohne Aufbau (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_montage_gesamt_geruest = fields.Float(
        string='Montage inkl. LKW an Gerüst (€)',
        compute='_compute_mietkalkulation', store=True
    )
    mk_montage_gesamt_gebaeude = fields.Float(
        string='Montage inkl. LKW an Gebäude (€)',
        compute='_compute_mietkalkulation', store=True
    )

    # ─── Preistabellen (hardcoded nach Preisliste 01/2023) ───────────────────
    _GRUNDPREIS = {
        '200': 640.0, '300': 680.0, '500': 750.0,
        '1000': 1040.0, '1500': 1190.0, '2000': 1240.0,
    }
    _MEHRPREIS_HOEHE = {
        '200': 13.0, '300': 14.0, '500': 18.0,
        '1000': 28.0, '1500': 31.0, '2000': 31.0,
    }
    _MEHRPREIS_STATION = {
        '200': 38.0, '300': 38.0, '500': 55.0,
        '1000': 55.0, '1500': 55.0, '2000': 55.0,
    }
    _MEHRPREIS_BUEHNE = {
        'keine': 0.0,
        '145x325': 60.0,
        '165x435': 80.0,
    }
    _MEHRPREIS_PERSON = {
        '200': 390.0, '300': 370.0, '500': 370.0,
        '1000': 450.0, '1500': 460.0, '2000': 460.0,
    }
    _STD_JE_5M = {
        '200': 1.0, '300': 1.5, '500': 1.8,
        '1000': 2.0, '1500': 2.5, '2000': 2.5,
    }
    # Rabattstaffeln: ab Monate → Prozent
    _RABATT_STAFFEL = [
        (12, 0.20), (6, 0.15), (4, 0.12), (3, 0.10), (2, 0.05), (0, 0.0),
    ]
    # LKW-Stundensatz für Transport
    _LKW_STUNDENSATZ = 140.0

    @api.depends(
        'mk_traglast', 'mk_aufbauhoehe', 'mk_buehnengroesse',
        'mk_personenbefoerderung', 'mk_extra_stationen',
        'mk_mietdauer_wochen', 'mk_transport_stunden',
        'mk_monteur_stundensatz', 'mk_helfer_stundensatz',
        'mk_std_je_station', 'mk_faktor_geruest', 'mk_faktor_gebaeude',
    )
    def _compute_mietkalkulation(self):
        for rec in self:
            traglast = rec.mk_traglast or '500'

            # ── Grundpreis ────────────────────────────────────────────────
            grundpreis = self._GRUNDPREIS.get(traglast, 0.0)
            rec.mk_grundpreis = grundpreis

            # ── Mehrhöhe ──────────────────────────────────────────────────
            basis_hoehe = 15.0
            schritt = 1.5
            extra_abschn = max(0, math.ceil((rec.mk_aufbauhoehe - basis_hoehe) / schritt))
            rec.mk_extra_hoehenabschnitte = extra_abschn
            mehrpreis_h = extra_abschn * self._MEHRPREIS_HOEHE.get(traglast, 0.0)
            rec.mk_mehrpreis_hoehe = mehrpreis_h

            # ── Stationen ─────────────────────────────────────────────────
            mehrpreis_st = rec.mk_extra_stationen * self._MEHRPREIS_STATION.get(traglast, 0.0)
            rec.mk_mehrpreis_stationen = mehrpreis_st

            # ── Bühne ─────────────────────────────────────────────────────
            mehrpreis_b = self._MEHRPREIS_BUEHNE.get(rec.mk_buehnengroesse or 'keine', 0.0)
            rec.mk_mehrpreis_buehne = mehrpreis_b

            # ── Personenbeförderung ───────────────────────────────────────
            mehrpreis_p = self._MEHRPREIS_PERSON.get(traglast, 0.0) if rec.mk_personenbefoerderung else 0.0
            rec.mk_mehrpreis_person = mehrpreis_p

            # ── Zwischensumme ─────────────────────────────────────────────
            zwischensumme = grundpreis + mehrpreis_h + mehrpreis_st + mehrpreis_b + mehrpreis_p
            rec.mk_zwischensumme = zwischensumme

            # ── Rabatt ────────────────────────────────────────────────────
            monate = rec.mk_mietdauer_wochen / 4.0
            rabatt = 0.0
            for grenze, satz in self._RABATT_STAFFEL:
                if monate >= grenze:
                    rabatt = satz
                    break
            rec.mk_rabatt_prozent = rabatt * 100.0

            preis_nach_rabatt = zwischensumme * (1.0 - rabatt)
            rec.mk_preis_nach_rabatt = preis_nach_rabatt

            # Verlängerungswoche = Preis nach Rabatt / 4 (Wochen)
            rec.mk_preis_verlaengerungswoche = preis_nach_rabatt / 4.0

            # ── Maschinenbruchversicherung 4% ─────────────────────────────
            maschinenbruch = preis_nach_rabatt * 0.04
            rec.mk_maschinenbruch = maschinenbruch

            # ── Gesamt pro 4 Wochen ───────────────────────────────────────
            rec.mk_gesamt_4wochen = preis_nach_rabatt + maschinenbruch

            # ── Montage ───────────────────────────────────────────────────
            std_je_5m = self._STD_JE_5M.get(traglast, 1.8)
            stunden_aufbau = (rec.mk_aufbauhoehe / 5.0) * std_je_5m
            rec.mk_stunden_aufbau = stunden_aufbau

            gesamt_stationen = 1 + rec.mk_extra_stationen  # EG+OG = 1 Einheit
            stunden_stationen = gesamt_stationen * rec.mk_std_je_station
            rec.mk_stunden_stationen = stunden_stationen

            gesamtstunden = stunden_aufbau + stunden_stationen
            rec.mk_gesamtstunden = gesamtstunden

            team_kosten_h = rec.mk_monteur_stundensatz + rec.mk_helfer_stundensatz
            rec.mk_team_kosten_stunde = team_kosten_h

            montage_geruest = gesamtstunden * team_kosten_h * rec.mk_faktor_geruest
            montage_gebaeude = gesamtstunden * team_kosten_h * rec.mk_faktor_gebaeude
            rec.mk_montage_geruest = montage_geruest
            rec.mk_montage_gebaeude = montage_gebaeude

            # ── Transport ─────────────────────────────────────────────────
            transport_kosten = rec.mk_transport_stunden * self._LKW_STUNDENSATZ
            rec.mk_transportkosten_lkw = transport_kosten

            rec.mk_montage_gesamt_geruest = montage_geruest + transport_kosten
            rec.mk_montage_gesamt_gebaeude = montage_gebaeude + transport_kosten
