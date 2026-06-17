# Sale Input Barcode

Odoo 19 module for Odoo.sh.

## Behavior
- Adds a field `Barcode Scan` to the sales order form.
- Scan a barcode into the field and end with `Enter`.
- The module finds the product by exact barcode.
- Each scan creates a **new** sale order line with quantity 1.
- The field is cleared after processing.

## Notes
- No scan button is required.
- Scanner should work in keyboard mode and append `Enter`.
- Test in a staging branch before production.
