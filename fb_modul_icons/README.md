# FB Modul Icons

## Übersicht

Dieses Modul stellt projektspezifische Modulsymbole für Odoo bereit und erweitert damit primär die visuelle Darstellung installierter Apps im Backend. Es eignet sich für individuelle Branding-Anpassungen oder zur besseren Wiedererkennbarkeit interner Custom-Module.

## Technische Eckdaten

| Feld | Wert |
|---|---|
| Technischer Name | `fb_modul_icons` |
| Zweck | Bereitstellung individueller Icons für Odoo-Module |
| Typischer Einsatz | Branding und visuelle Differenzierung von Custom-Modulen |

## Funktionsumfang

- Bereitstellung eigener Modul-Icons für das Odoo-Backend.
- Verbesserung der visuellen Wiedererkennbarkeit interner Erweiterungen.
- Saubere Trennung von Branding-Ressourcen und fachlicher Business-Logik.

## Erwartete Struktur

In solchen Modulen liegen die relevanten Dateien üblicherweise in einem `static`-Verzeichnis, zum Beispiel für Icons oder sonstige grafische Ressourcen. Falls zusätzlich Manifest-Metadaten gepflegt werden, erfolgt die Einbindung der Icons über die übliche Odoo-Modulstruktur.

## Installation

1. Das Modul in den konfigurierten Addons-Pfad legen.
2. Die App-Liste in Odoo aktualisieren.
3. Das Modul installieren oder bei bestehender Installation upgraden.

## Hinweise

Wenn weitere Custom-Module eigene Icons erhalten sollen, sollten Benennung, Dateipfade und Ablagekonventionen konsistent gehalten werden. So bleibt die Wartung auch bei mehreren projektspezifischen Erweiterungen übersichtlich.
