## ol_invoice_report_changes

ol_invoice_report_changes ist ein Odoo-19-Modul für angepasste Rechnungs-, Angebots- und Auftragsdokumente im Fischbacher-Kontext.
 Es überschreibt vor allem Report-Templates, Druckaktionen, Layouts und ausgewählte Formularansichten, statt eigene Geschäftslogik in größerem Umfang einzuführen.

## Überblick
Das Modul trägt den Namen Invoice Report Change, hat die Version 19.0.1.0.0 und steht unter der Lizenz LGPL-3.
 Es ist der Kategorie Account zugeordnet und beschreibt sich selbst knapp als „Changes on the invoice report“.

## Abhängigkeiten
Das Modul hängt von base, account, l10n_din5008, sale, mail, sale_pdf_quote_builder und sale_subscription ab.
 Dadurch ist klar, dass es nicht nur klassische Rechnungen, sondern auch Verkaufsdokumente, Pro-forma-Dokumente und Abo-/Rental-nahe Druckbilder beeinflusst.

## Funktionsumfang
Der Schwerpunkt liegt auf individuellen Drucklayouts für Angebote, Aufträge, Pro-forma-Rechnungen und Rechnungen.
 Die geladenen XML-Dateien decken Papierformat, Report-Actions, External Layout, Sale-Order-Reports, Confirmation-Reports, Preview, Partneransichten und zusätzliche Mail-Templates ab.

In den Report-Actions werden Drucknamen dynamisch gesetzt, etwa für „Rental Quote“, „Rental Order“, „Pro-Forma Invoice“ oder „Rental Invoice“, abhängig von Feldern wie is_subscription, plan_id, has_plan und dem Dokumentstatus.
 Das Modul unterscheidet also sichtbar zwischen normalen Verkaufsbelegen und Abo-/Mietprozessen.

## Technische Struktur
Die zentrale Moduldefinition lädt unter anderem views/paperformat.xml, views/report_action.xml, views/external_layout.xml, views/account_move_report.xml, views/pro_forma_invoice_quotation_report.xml, views/sale_order_report.xml, views/sale_order_confirmation_report.xml, views/sale_order.xml, views/sale_order_preview.xml und views/res_partner_view.xml.
 Zusätzlich wird data/mail_template_data.xml eingebunden.

Die Sale-Order-Erweiterung ergänzt Felder wie purchase_no, client_order_number, lease_agreement_no, client_order_name und hide_total in der Auftragsmaske.
 In den Report-Templates werden außerdem projekt- und kundenbezogene Daten, Zahlungsbedingungen sowie differenzierte Überschriften für Quote, Order und Rental-Dokumente ausgegeben.

## Hinweise für Entwicklung
Das Modul ist besonders relevant, wenn Layout-Anpassungen an QWeb-Reports nachvollzogen oder erweitert werden sollen.
 Änderungen an Dokumentlogik sollten bevorzugt in den vorhandenen Report-XML-Dateien und Report-Actions erfolgen, weil dort der Großteil der Fachlogik für die Ausgabe liegt.
