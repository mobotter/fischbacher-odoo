# FB Fixed Putaway (Odoo 19)

Autor: Moritz Kern  
Firma: Fischbacher GmbH + Co. KG

## Zweck

Vorschau und Erstellung produktspezifischer Odoo-Einlagerungsregeln aus vorhandenen positiven Bestandspositionen. Eine Regel bleibt erhalten, wenn der Bestand später 0 ist. Das Modul ändert keine Bestände, Routen oder offenen Transfers.

## Installation

Ordner `fb_fixed_putaway` ins Odoo.sh-Addons-Repository legen, App-Liste aktualisieren und das Modul installieren. Vor produktiver Nutzung in Staging installieren und einen echten neuen Wareneingang testen.

## Bedienung

Unter Lager > Konfiguration > Feste Einlagerungsregeln den Eingangsort (`WH/Stock`) prüfen, optional ein Produkt auswählen und "Vorschau laden" klicken. Eindeutige Bestandsorte werden zur Übernahme markiert. Bei mehreren Fachorten, nur Sammelort-/Mietparkbestand oder Bestand 0 ist ein Ort von Hand zu wählen und die Zeile zu markieren. "Markierte Regeln erstellen" erzeugt die Regeln. Im Produktformular öffnet der Button den Assistenten für die einzige Produktvariante.

## Sicherheit

Bestehende Regeln bleiben unverändert. Das Mietpark Lager mit ID 8 ist als Ziel ausgeschlossen. Keine automatische Bestandsumbuchung. Berechtigung: Lageradministrator. Die Regel gilt für Bewegungen, deren Eingangsort dem Feld `location_in_id` entspricht; Mietrückgaben mit Ziel ID 8 sind nicht enthalten.

## Prüfung vor Produktivbetrieb

Installations- und End-to-End-Test auf Odoo.sh-Staging erforderlich. Der Assistent nutzt Odoo-19-Modellfelder `stock.putaway.rule.product_id`, `location_in_id`, `location_out_id` und das Feld `product.product.is_storable`. Bei Variantenartikeln wird keine einzelne Vorlage automatisch auf mehrere Varianten übertragen.
