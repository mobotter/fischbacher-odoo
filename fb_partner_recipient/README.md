# Leistungsempfänger (fb_partner_recipient)

**Autor:** Moritz Kern · **Firma:** Fischbacher GmbH + Co. KG · **Version:** Odoo 19.0 · **Lizenz:** LGPL-3

## Funktionen

### Kontakte (`res.partner`)
- Neuer Adresstyp **Leistungsempfänger** (`type = 'recipient'`) als zusätzlicher Radiobutton neben Kontakt, Rechnungsadresse, Lieferadresse und Andere Adresse.
- Unterkontakte ohne Namen werden wie die Standard-Adresstypen als „Firma, Leistungsempfänger“ angezeigt.
- Helfer `_get_recipient_address()` nutzt die Standardlogik `address_get(['recipient'])` (Fallback: Kontakt bzw. der Partner selbst).

### Angebote / Aufträge (`sale.order`)
- Neues Feld **Leistungsempfänger** (`partner_recipient_id`) direkt unter der Lieferadresse.
- Wird bei Kundenwahl automatisch vorbelegt (Unterkontakt mit Typ Leistungsempfänger, sonst der Kunde), bleibt aber manuell änderbar.
- Wird in die Rechnung (`_prepare_invoice`, inkl. Anzahlungsrechnungen) und in die Lieferscheine übernommen.
- Änderungen am Auftrag werden auf offene Lieferscheine übertragen.
- Suchfeld in der Auftragssuche; Änderungen werden im Chatter protokolliert.

### Adressfelder im Angebot / Auftrag
- Das Feld Kunde (`partner_id`) bleibt unverändert.
- Rechnungsadresse, Lieferadresse und Leistungsempfänger werden nur angezeigt, wenn der Kunde untergeordnete Kontakte dieser Adressart hat.
- Die Dropdowns bieten nur diese Unterkontakte an (Typ Rechnungsadresse, Lieferadresse bzw. Leistungsempfänger), nicht alle Kontakte.
- Ist ein Feld ausgeblendet, bleibt der automatisch berechnete Wert erhalten (Standard: der Kunde selbst).

### Lieferscheine (`stock.picking`)
- Feld **Leistungsempfänger** unter dem Partner, sichtbar bei Ausgängen.
- Wert kommt aus dem Verkaufsauftrag, bei manuellen Lieferscheinen aus dem Partner.

### Rechnungen / Gutschriften (`account.move`)
- Feld **Leistungsempfänger** unter der Lieferadresse (nur Ausgangsrechnungen, Gutschriften, Belege).
- Nur im Entwurf änderbar; wird bei Gutschriften mitkopiert.

## Installation
1. Ordner `fb_partner_recipient` ins Addons-Verzeichnis (bei Odoo.sh: ins Repository) kopieren.
2. Apps → „Apps-Liste aktualisieren“ → **Leistungsempfänger** installieren.

## Abhängigkeiten
`sale_stock`, `account`

## Hinweise
- Die Felder für Rechnungs- und Lieferadresse in Angebot/Rechnung sind im Standard nur mit der Einstellung „Kunden-Adressen“ (Gruppe `account.group_delivery_invoice_address`) sichtbar. Das Feld Leistungsempfänger ist immer sichtbar.
- Beim Deinstallieren werden Kontakte vom Typ Leistungsempfänger auf „Kontakt“ zurückgesetzt.
