# Rechnungen und Stornogutschriften im Verkaufs-Smartbutton

Autor: Moritz Kern  
Firma: Fischbacher GmbH + Co. KG  
Version: Odoo 19.0 / LGPL-3

## Zweck
Der Rechnungs-Smartbutton eines Verkaufsauftrags bzw. Abonnements zeigt neben
seinen bisherigen Belegen auch direkt zugeordnete Kundengutschriften an:
`account.move.reversed_entry_id` verweist auf eine der ursprünglichen
Kundenrechnungen im Standardfeld `sale.order.invoice_ids`.

## Verhalten
- Bestehende Belege bleiben enthalten; Recordset-Vereinigung vermeidet Duplikate.
- Ergänzung ausschließlich für `move_type = out_refund`.
- Entwürfe und stornierte Belege werden nicht zusätzlich ausgefiltert.
- Keine Suche über Kunde oder freien Ursprungstext.
- Keine rekursive Suche nach Stornierungen von Stornierungen.
- Keine Änderung von Standardfeldern invoice_ids/invoice_count, Rechnungspositionen,
  Buchungen, Rechnungsstatus oder Abrechnungsberechnungen.
- Separate nicht gespeicherte Felder für Anzeige und Zähler.
- Keine sudo-Abfragen; bestehende Zugriffsregeln gelten weiterhin.
- Gilt für alle Verkaufsaufträge, einschließlich Abonnements.
- Öffnet eine eigene Belegaktion ohne übernommene search_default-Filter.

## Installation
1. ZIP entpacken und den Modulordner in einen Odoo-Addons-Pfad kopieren.
2. Odoo neu starten, App-Liste aktualisieren und das Modul installieren.
3. Bei Odoo.sh den Modulordner im Addons-Repository einchecken und deployen.
4. Zuerst in einer Testdatenbank prüfen. Auf reinem Odoo Online lassen sich
   gewöhnliche Python-Addons nicht installieren.

## Konkreter Prüffall
Abo S00861 / ID 863 enthält bisher die Beleg-IDs 38179, 22758, 27726, 32695.
Gutschrift 45384 / RINV/2026/00077 verweist über reversed_entry_id auf 38179.
Erwartet: fünf Belege, sofern dieselben Benutzerrechte gelten und keine weiteren
passenden Gutschriften vorliegen. Bereits verknüpfte Gutschriften dürfen nicht
doppelt gezählt werden. Fremde Kundengutschriften dürfen nicht erscheinen.

## Testcheckliste
- S00861 öffnen: Zähler und Liste einschließlich RINV/2026/00077 prüfen.
- Auftrag ohne Gutschrift: bisherige Beleganzahl prüfen.
- Bereits über Positionen verknüpfte Gutschrift: keine Doppelzählung.
- Unabhängige Gutschrift desselben Kunden: nicht aufgenommen.
- Benutzer mit eingeschränkten Buchhaltungsrechten separat prüfen.
- Abo-Abrechnung und Standardfeld invoice_ids bleiben unverändert.

## Kompatibilität
Erbt sale.view_order_form. Anpassungen anderer Module am selben Button können
View-Konflikte verursachen. Nicht gegen die konkrete Kundendatenbank getestet.
