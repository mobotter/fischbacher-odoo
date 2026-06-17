# Sale Input Barcode

Odoo 19 module for Odoo.sh.

## Behavior
- Adds a barcode area above sale order lines.
- Scan a product barcode into the field.
- Click "Scan übernehmen" or press Enter in the field depending on form behavior.
- Each processed barcode creates a new sale order line with quantity 1.
- The scan field is cleared after processing.

## Notes
- This version avoids backend JS assets for Odoo.sh stability.
- For fully automatic scan processing without clicking, a small frontend extension is still needed.
