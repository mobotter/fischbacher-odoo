# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'DIN 5008 - Sale Fischbacher',
    'version': '19.0.1.0.0',
    'summary': 'Fischbacher Corporate Design für DIN5008-Dokumente (Angebote, Rechnungen)',
    'description': """
Dieses Modul passt das Odoo 19 Standard-DIN5008-Layout (für Angebote, Rechnungen etc.) an das Corporate Design der Fischbacher GmbH an.

Detaillierte Anpassungen:
=========================
1. Adressfenster (Absenderzeile):
   - Kompakte, einzeilige Darstellung der Absenderdaten (Name | Straße | PLZ | Ort) in 9px.
   - Eine dezente Trennlinie schließt die Absenderzeile nach unten ab.

2. Dokumententitel & Typografie:
   - Die Hauptüberschriften (z. B. "Rechnung", Angebotsnummer) werden in der blauen Hausfarbe (#0069b4) dargestellt.

3. Footer (Fußzeile):
   - Vollständig neues, dreispaltiges Layout im unteren Seitenbereich.
   - Spalte 1: Hausanschrift (aus den Unternehmensdetails).
   - Spalte 2: Kontaktdaten (Festes Layout für Telefon und Telefax mit blauen Labels).
   - Spalte 3: Bankverbindungen (Automatischer Abruf von bis zu zwei Banken inkl. IBAN und BIC).
   - Vollständiger rechtlicher Firmenblock (Kommanditgesellschaft, Sitz, HRA/HRB, Geschäftsführer, Steuernummern) in 9px.
   - Dynamische Seitenzahlen ("Page X of Y") rechtsbündig integriert.

4. Tabellen-Styling:
   - Angebots- und Rechnungszeilen (Tabellenköpfe) erhalten angepasste Linien (border-bottom in Hausfarbe #0069b4 oder grau) zur besseren Strukturierung.
    """,
    'author': 'Odolution',
    'license': 'LGPL-3',
    'category': 'Accounting/Localizations',
    'depends': [
        'l10n_din5008',
    ],
    'data': [
        'report/external_layout_fischbacher.xml',
    ],
    'auto_install': True,
}
