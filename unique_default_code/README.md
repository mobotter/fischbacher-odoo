# Product Variant Default Code Unique Editable Optional

Dieses Modul macht `default_code` auf `product.product` editierbar, optional und eindeutig.

## Verhalten
- `default_code` darf leer bleiben.
- Das Feld ist im Formular editierbar.
- Doppelte nicht-leere Codes werden beim Speichern blockiert.

## Hinweis
Falls ein anderes Modul, Studio oder eine View-Erweiterung das Feld weiterhin als Pflichtfeld oder readonly markiert, muss diese Logik ebenfalls entfernt werden.
