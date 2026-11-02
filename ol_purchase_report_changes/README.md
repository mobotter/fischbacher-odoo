Purchase Order Report Changes
=============================

Autor: Moritz Kern  
Firma: Fischbacher GmbH + Co. KG

Überblick
---------

Dieses Modul passt den PDF-Bericht für Einkaufsbestellungen in Odoo 19 an.
Das Layout orientiert sich am benutzerdefinierten Rechnungsbericht aus dem
Modul `ol_invoice_report_changes`.

Funktionen
----------

- Einheitliches Kopf- und Fußlayout aus `ol_invoice_report_changes`
- DIN-5008-orientierte Lieferantenanschrift
- Informationsblock mit Bestellnummer, Bestelldatum, Lieferdatum,
  Lieferantenreferenz und Einkäufer
- Überarbeitete Bestellpositions-Tabelle
- Darstellung von Abschnitten und Notizen
- Einheitliche Summenübersicht
- Verwendung des benutzerdefinierten DIN-5008-Papierformats

Abhängigkeiten
--------------

- purchase
- ol_invoice_report_changes

Installation
------------

1. Das Modulverzeichnis `ol_purchase_report_changes` in den Addons-Pfad legen.
2. Odoo-App-Liste aktualisieren.
3. Das Modul „Purchase Order Report Changes“ installieren oder aktualisieren.
4. Eine Anfrage oder Bestellung öffnen.
5. Über Drucken den Bericht erzeugen und Layout sowie Seitenumbrüche prüfen.

Technische Hinweise
-------------------

Das Modul erbt die Odoo-QWeb-Vorlage
`purchase.report_purchaseorder_document`. Es ersetzt ausschließlich den
Dokumentinhalt und verwendet das gemeinsame externe Layout
`ol_invoice_report_changes.external_layout_for_invoice`.

Das Papierformat wird an der Standard-Reportaktion des Einkauf-Moduls auf
`ol_invoice_report_changes.report_invoice_custom_paperformat` gesetzt.
