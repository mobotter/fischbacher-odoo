# Order Line Search & Reporting (Odoo 19)

Dieses Modul erweitert das Odoo-Verkaufsmodul (Sales) um eine dedizierte und detaillierte Ansicht für alle Auftragspositionen (Sale Order Lines). Es richtet sich an Vertriebsmitarbeiter, den Support und Administratoren, die schnell und effizient in der Historie von Verkaufsaufträgen nach bestimmten Artikeln, Kunden oder Preisen recherchieren müssen.

## 🌟 Hauptfunktionen

### 1. Zentrales Berichtswesen
- **Neuer Menüpunkt:** Zu finden unter *Verkauf -> Berichtswesen -> Auftragszeilen*.
- **Flache Listenansicht:** Alle Auftragspositionen werden in einer übersichtlichen, flachen Liste (ohne störende Standardgruppierung) dargestellt.

### 2. Intelligente Smart-Buttons
- **Kundenansicht (`res.partner`):** Ein neuer Smart-Button oben rechts öffnet alle Auftragspositionen, die jemals für diesen Kunden (inkl. Unterkontakten) erfasst wurden.
- **Produktansicht (`product.template` & `product.product`):** Ein neuer Smart-Button (Einkaufswagen-Symbol) öffnet sofort alle Auftragspositionen, in denen das jeweilige Produkt verkauft wurde.

### 3. Erweiterte Ansichten & Spalten
Die neu gestaltete Listenansicht bietet maximale Transparenz und verzichtet auf platzraubende Währungsspalten. Folgende Daten sind direkt einsehbar:
- **Auftragsreferenz** und klickbarer Link zum Originalauftrag
- **Kunde**
- **Verkaufsdatum** (Erstelldatum des Auftrags)
- **Beschreibung**
- **Vertriebsmitarbeiter**
- **Menge** und **Rabatt (%)**
- **Verkaufspreis** (inkl. Währungssymbol)
- **Einkaufspreis** (Kosten des Produkts zum schnellen Margen-Check)
- **Route** (die auftragsspezifische Route, z.B. Streckengeschäft)
- **Auftragsstatus** (Farbige Badges zur schnellen Identifikation)

### 4. Schnelle Navigation (Quick-Actions)
Am Ende jeder Tabellenzeile befinden sich drei Icon-Buttons, die es erlauben, ohne Umwege direkt in die verknüpften Datensätze zu springen:
- 📦 **Produkt öffnen**
- 👤 **Kunde öffnen**
- 📄 **Auftrag öffnen**

### 5. Optimierte Such- & Filterfunktionen
- Suchleiste erweitert um die Möglichkeit, direkt nach *Artikelnummer (Interne Referenz)*, *Produktname* oder *Kunde* zu suchen.
- Vorkonfigurierte Filter zur schnellen Gruppierung nach Kunde oder Produkt (manuell aktivierbar).

## 🛠 Technische Details & Abhängigkeiten

- **Odoo Version:** 19.0
- **Abhängigkeiten:** `base`, `sale`, `sale_management`, `sale_stock`
- **Architektur:** Reine Erweiterung bestehender Modelle (`sale.order.line`, `res.partner`, `product.template`, `product.product`), ohne tiefe Eingriffe in die Geschäftslogik. Die Views sind "Read-Only", um versehentliche Änderungen aus dem Berichtswesen heraus zu verhindern.

## 🚀 Installation & Update

Da das Modul Python-Logik (für die Smart-Buttons und Custom-Fields) enthält, erfordert die Installation einen Neustart des Odoo-Dienstes.

```bash
# 1. Modul in den addons_path kopieren
# 2. Odoo-Dienst neu starten
sudo systemctl restart odoo

# 3. Datenbank aktualisieren
odoo-bin -d <datenbankname> -u order_line_search --stop-after-init
```

## 👨‍💻 Autor & Wartung

Entwickelt und gewartet von **Moritz Kern**.  
Code & Historie: [GitHub Repository](https://github.com/Fischbacher-GmbH-Co-KG/odoo/tree/main/order_line_search)
