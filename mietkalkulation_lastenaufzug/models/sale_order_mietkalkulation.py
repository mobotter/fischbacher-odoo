# -*- coding: utf-8 -*-
import math
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ── Eingaben ──────────────────────────────────────────────────────────────
    mk_traglast = fields.Selection(
        selection=[
            ('200', '200 kg'),
            ('300', '300 kg'),
            ('500', '500 kg'),
            ('1000', '1000 / 1200 kg'),
            ('1500', '1500 kg'),
            ('2000', '2000 kg'),
        ],
        string='Traglast (kg)',
        default='500',
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
    mk_personenbefoerderung = fields.Boolean(
        string='Personenbeförderung',
        default=False,
    )
    mk_extra_stationen = fields.Integer(
        string='Zusätzl. Be-/Entladestellen (über EG+OG)',
        default=0,
    )
    mk_mietdauer_wochen = fields.Integer(
        string='Mietdauer (Wochen)',
        default=16,
    )
    mk_transport_stunden = fields.Float(
        string='Transport LKW (Stunden)',
        default=2.0,
    )
    # Montage-Einstellwerte
    mk_monteur_stundensatz = fields.Float(
        string='Monteur Stundensatz (€)',
        default=88.0,
    )
    mk_helfer_stundensatz = fields.Float(
        string='Helfer Stundensatz (€)',
        default=42.0,
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

    # ── Berechnungsfelder (compute + store) ────────────────────────────────────
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
        string='Rabatt % (nach Mietdauer)',
        compute='_compute_mk',
        store=True,
    )
    mk_preis_nach_rabatt = fields.Float(
        string='Preis nach Rabatt (€)',
        compute='_compute_mk',
        store=True,
    )
    mk_preis_verlaengerungswoche = fields.Float(
        string='Preis Verlängerungswoche (€)',
        compute='_compute_mk',
        store=True,
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
        string='Gesamtstunden Team',
        compute='_compute_mk',
        store=True,
    )
    mk_team_kosten_stunde = fields.Float(
        string='Teamkosten pro Stunde (€)',
        compute='_compute_mk',
        store=True,
    )
    mk_montage_geruest = fields.Float(
        string='Montagekosten an Gerüst (€)',
        compute='_compute_mk',
        store=True,
    )
    mk_montage_gebaeude = fields.Float(
        string='Montagekosten an Gebäude (€)',
        compute='_compute_mk',
        store=True,
    )
    mk_transportkosten_lkw = fields.Float(
        string='Transportkosten LKW (€)',
        compute='_compute_mk',
        store=True,
    )
    mk_montage_gesamt_geruest = fields.Float(
        string='Montage inkl. LKW an Gerüst (€)',
        compute='_compute_mk',
        store=True,
    )
    mk_montage_gesamt_gebaeude = fields.Float(
        string='Montage inkl. LKW an Gebäude (€)',
        compute='_compute_mk',
        store=True,
    )

    # ── Preistabellen (Preisliste 01/2023) ─────────────────────────────────────
    _MK_GRUNDPREIS = {
        '200': 640.0, '300': 680.0, '500': 750.0,
        '1000': 1040.0, '1500': 1190.0, '2000': 1240.0,
    }
    _MK_MEHRPREIS_HOEHE = {
        '200': 13.0, '300': 14.0, '500': 18.0,
        '1000': 28.0, '1500': 31.0, '2000': 31.0,
    }
    _MK_MEHRPREIS_STATION = {
        '200': 38.0, '300': 38.0, '500': 55.0,
        '1000': 55.0, '1500': 55.0, '2000': 55.0,
    }
    _MK_MEHRPREIS_BUEHNE = {
        'keine': 0.0, '145x325': 60.0, '165x435': 80.0,
    }
    _MK_MEHRPREIS_PERSON = {
        '200': 390.0, '300': 370.0, '500': 370.0,
        '1000': 450.0, '1500': 460.0, '2000': 460.0,
    }
    _MK_STD_JE_5M = {
        '200': 1.0, '300': 1.5, '500': 1.8,
        '1000': 2.0, '1500': 2.5, '2000': 2.5,
    }
    # Rabattstaffeln: (ab Monate, Prozentsatz)
    _MK_RABATT = [
        (12, 0.20), (6, 0.15), (4, 0.12),
        (3, 0.10), (2, 0.05), (0, 0.0),
    ]
    _MK_LKW_STUNDENSATZ = 140.0

    @api.depends(
        'mk_traglast', 'mk_aufbauhoehe', 'mk_buehnengroesse',
        'mk_personenbefoerderung', 'mk_extra_stationen',
        'mk_mietdauer_wochen', 'mk_transport_stunden',
        'mk_monteur_stundensatz', 'mk_helfer_stundensatz',
        'mk_std_je_station', 'mk_faktor_geruest', 'mk_faktor_gebaeude',
    )
    def _compute_mk(self):
        for rec in self:
            tl = rec.mk_traglast or '500'

            # Grundpreis
            grundpreis = self._MK_GRUNDPREIS.get(tl, 0.0)
            rec.mk_grundpreis = grundpreis

            # Mehrhöhe
            extra_abschn = max(0, math.ceil(
                (rec.mk_aufbauhoehe - 15.0) / 1.5
            ))
            rec.mk_extra_hoehenabschnitte = extra_abschn
            meh = extra_abschn * self._MK_MEHRPREIS_HOEHE.get(tl, 0.0)
            rec.mk_mehrpreis_hoehe = meh

            # Stationen
            mes = rec.mk_extra_stationen * self._MK_MEHRPREIS_STATION.get(tl, 0.0)
            rec.mk_mehrpreis_stationen = mes

            # Buehne
            meb = self._MK_MEHRPREIS_BUEHNE.get(rec.mk_buehnengroesse or 'keine', 0.0)
            rec.mk_mehrpreis_buehne = meb

            # Person
            mep = self._MK_MEHRPREIS_PERSON.get(tl, 0.0) if rec.mk_personenbefoerderung else 0.0
            rec.mk_mehrpreis_person = mep

            # Zwischensumme
            zs = grundpreis + meh + mes + meb + mep
            rec.mk_zwischensumme = zs

            # Rabatt
            monate = rec.mk_mietdauer_wochen / 4.0
            rabatt = 0.0
            for grenze, satz in self._MK_RABATT:
                if monate >= grenze:
                    rabatt = satz
                    break
            rec.mk_rabatt_prozent = rabatt * 100.0

            pnr = zs * (1.0 - rabatt)
            rec.mk_preis_nach_rabatt = pnr
            rec.mk_preis_verlaengerungswoche = pnr / 4.0

            # Maschinenbruch
            mb = pnr * 0.04
            rec.mk_maschinenbruch = mb
            rec.mk_gesamt_4wochen = pnr + mb
            rec.mk_gesamt_mietdauer = (pnr + mb) * (rec.mk_mietdauer_wochen / 4.0)

            # Montage
            std_je_5m = self._MK_STD_JE_5M.get(tl, 1.8)
            st_aufbau = (rec.mk_aufbauhoehe / 5.0) * std_je_5m
            rec.mk_stunden_aufbau = st_aufbau

            gesamt_stat = 1 + rec.mk_extra_stationen
            st_stat = gesamt_stat * rec.mk_std_je_station
            rec.mk_stunden_stationen = st_stat

            ges_std = st_aufbau + st_stat
            rec.mk_gesamtstunden = ges_std

            team_h = rec.mk_monteur_stundensatz + rec.mk_helfer_stundensatz
            rec.mk_team_kosten_stunde = team_h

            mon_g = ges_std * team_h * rec.mk_faktor_geruest
            mon_geb = ges_std * team_h * rec.mk_faktor_gebaeude
            rec.mk_montage_geruest = mon_g
            rec.mk_montage_gebaeude = mon_geb

            transport = rec.mk_transport_stunden * self._MK_LKW_STUNDENSATZ
            rec.mk_transportkosten_lkw = transport
            rec.mk_montage_gesamt_geruest = mon_g + transport
            rec.mk_montage_gesamt_gebaeude = mon_geb + transport
