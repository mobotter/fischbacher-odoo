# Invoice Address Email for Partner

Dieses Odoo-Modul erweitert das Modell `res.partner` um zusätzliche Felder und Logik für Rechnungsadressen sowie Werbe-/Marketing-E-Mail-Verwaltung. Es verbindet Kontaktpflege, Rechnungs-E-Mail und Werbeausschluss in einem kompakten Zusatzmodul.

## Funktionen

Das Modul ergänzt das Partner-Modell um folgende Felder:

- `invoice_address_email` – E-Mail-Adresse der Rechnungsadresse
- `invoice_email_manual` – manuelle Rechnungs-E-Mail
- `advertising_exclusion` – Ausschluss von Werbe-E-Mails
- `advertising_email` – Werbe-/Marketing-E-Mail-Adresse

Zusätzlich erweitert das Modul die Kontaktansicht in Odoo und fügt die Felder direkt im Partnerformular ein. Die Felder werden per View-Inheritance in `base.view_partner_form` ergänzt.

## Rechnungs-E-Mail

Die Rechnungs-E-Mail wird aus dem zugehörigen Kindkontakt vom Typ `invoice` abgeleitet. Wenn bereits ein Rechnungsadress-Kontakt existiert, wird dessen E-Mail gelesen und in das Feld `invoice_address_email` übernommen.

Wird `invoice_address_email` geändert, aktualisiert das Modul die vorhandene Rechnungsadresse oder legt automatisch einen neuen untergeordneten Kontakt mit Typ `invoice` an. Dabei werden Stammdaten wie Adresse, Land und Bundesland vom Hauptpartner übernommen.

## Werbe-E-Mail und Blacklist

Beim Erstellen eines Partners wird `advertising_email` automatisch mit der normalen E-Mail-Adresse vorbelegt, sofern kein eigener Wert gesetzt wurde. Beim späteren Schreiben wird diese ebenfalls nachgezogen, wenn noch keine separate Werbe-E-Mail gepflegt ist.

Das Feld `advertising_exclusion` steuert die Synchronisation mit der Odoo-Mail-Blacklist. Ist der Wert aktiv, wird die normalisierte Werbe-E-Mail zur `mail.blacklist` hinzugefügt; wird der Ausschluss entfernt, wird der Eintrag aus der Blacklist gelöscht.

Zusätzlich erweitert das Modul den Unblacklist-Wizard von Odoo. Wird eine Adresse über den Wizard aus der Blacklist entfernt, setzt das Modul bei passenden Partnern `advertising_exclusion` zurück und schreibt eine interne Nachricht ins Chatter-Protokoll.

## Server Action

Das Modul liefert eine Server Action **Update Partner Emails** mit. Diese Aktion ist am Modell `res.partner` gebunden und kann genutzt werden, um `advertising_email` aus der normalen Partner-E-Mail zu übernehmen.

## Technische Details

- Modulname: `Invoice Address Email for Partner`
- Version: `18.1`
- Abhängigkeiten: `base`, `mail`
- Lizenz: `LGPL-3`
- Formularansicht: Erweiterung von `base.view_partner_form`

## Installation

1. Modul in das Addons-Verzeichnis kopieren.
2. Apps-Liste in Odoo aktualisieren.
3. Nach **Invoice Address Email for Partner** suchen.
4. Modul installieren.

## Enthaltene Dateien

```text
your_module/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── res_partner.py
├── views/
│   └── res_partner_view.xml
└── security/
    └── server_action.xml
```

## Einsatzbereich

Das Modul eignet sich für Unternehmen, die Rechnungs-E-Mails getrennt von allgemeinen Kontakt-E-Mails pflegen möchten und gleichzeitig sicherstellen wollen, dass Werbesperren sauber mit der Odoo-Blacklist synchronisiert bleiben. Besonders nützlich ist das in CRM-, Vertriebs- und Accounting-nahen Prozessen mit getrennten Ansprechpartnern für Buchhaltung und Marketing.

## Hinweise

Das Manifest nennt Version `18.1`, während in den XML-Kommentaren ein Hinweis auf Odoo 19 auftaucht, weil ein altes `telefax`-Feld dort nicht mehr existiert. Vor produktivem Einsatz sollte deshalb geprüft werden, ob das Modul tatsächlich für Odoo 18 oder Odoo 19 gedacht ist und ob Versionsnummer, Kommentarstand und Zielsystem zusammenpassen.
