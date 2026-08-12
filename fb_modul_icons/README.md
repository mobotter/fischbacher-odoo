# FB Modul Icons 🎨

## Übersicht

Dieses Modul stellt projektspezifische Modulsymbole für Odoo bereit und erweitert damit primär die visuelle Darstellung installierter Apps im Backend. Es eignet sich für individuelle Branding-Anpassungen oder zur besseren Wiedererkennbarkeit interner Custom-Module.

---

## Technische Eckdaten

| Feld | Wert |
|---|---|
| **Technischer Name** | `fb_modul_icons` |
| **Zweck** | Bereitstellung individueller Icons für Odoo-Module |
| **Typischer Einsatz** | Branding und visuelle Differenzierung von Custom-Modulen |
| **Kompatibilität** | Odoo 19 |

---

## Funktionsumfang

- 📦 Bereitstellung eigener Modul-Icons für das Odoo-Backend.
- 🎯 Verbesserung der visuellen Wiedererkennbarkeit interner Erweiterungen.
- 🛠️ Saubere Trennung von Branding-Ressourcen und fachlicher Business-Logik.
- 🔗 Einfache Verlinkung von Haupt-Dashboards (z. B. direkter Absprung auf "Verkauf > Produkte").

---

## Verzeichnis- & Dateistruktur

Um sicherzustellen, dass Odoo die Icons korrekt erkennt und lädt, muss folgende Struktur zwingend eingehalten werden:

```text
fb_modul_icons/
├── __manifest__.py
├── README.md
├── views/
│   └── menu_views.xml           # Definition der Menüs und Aktionen
└── static/
    └── description/
        ├── icon.png             # Icon für den Odoo App Store (falls benötigt)
        └── products_icon.png    # Custom App-Icon für das Dashboard
```

In diesem Modul liegen die relevanten grafischen Dateien im `static/description/`-Verzeichnis. Die Einbindung der Icons erfolgt über XML-Menüeinträge (Feld `web_icon`).

---

## Einrichtungs-Beispiel (Dashboard Icon)

Wenn du ein neues Icon direkt auf dem Odoo 19 Haupt-Dashboard anzeigen möchtest, definiere das Menü **ohne ein Parent-Menü** in der XML und referenziere das Bild wie folgt:

```xml
<record id="menu_dashboard_sales_products" model="ir.ui.menu">
    <field name="name">Produkte</field>
    <field name="sequence">15</field>
    <field name="action" ref="action_dashboard_sales_products"/>
    <field name="web_icon">fb_modul_icons,static/description/products_icon.png</field>
</record>
```

---

## Installation & Deployment

1. Klone oder kopiere dieses Modul in den konfigurierten Odoo `addons`-Pfad.
2. Aktiviere in Odoo den Entwicklermodus (Developer Mode).
3. Navigiere zu *Apps* und klicke auf **App-Liste aktualisieren (Update Apps List)**.
4. Suche nach `fb_modul_icons` und klicke auf **Installieren** (oder **Upgrade**, falls bereits installiert).
5. **Wichtig:** Lade dein Browserfenster (F5 / Strg+R) komplett neu, damit der Cache für die App-Icons im Dashboard neu aufgebaut wird.

---

## Hinweise & Best Practices

- **Konsistenz:** Wenn weitere Custom-Module eigene Icons erhalten sollen, sollten Benennung, Dateipfade und Ablagekonventionen konsistent in diesem Modul gebündelt werden. So bleibt die Wartung übersichtlich.
- **Icon-Format:** Odoo bevorzugt `PNG`- oder `SVG`-Dateien. Die typische Größe für Dashboard-Icons und das App-Store-Icon beträgt `256x256` oder `512x512` Pixel.
- **Troubleshooting:** Sollte ein Icon nicht angezeigt werden:
  - Prüfe, ob der Dateipfad in der XML zu 100% korrekt geschrieben ist.
  - Prüfe, ob der Modulname im `web_icon`-String stimmt (`fb_modul_icons,...`).
  - Führe einen Hard-Refresh im Browser durch, um Cache-Probleme auszuschließen.
