# Sale Input Barcode

Odoo 19 module for Odoo.sh.

## Goal
When a product is selected in the sale order line product many2one field, automatically add the next line and focus the next product input.

## Intended behavior
- Scan barcode into the product field or type/select a product.
- As soon as Odoo accepts the product selection, a new line is added.
- The next product input gets focus automatically.

## Notes
- This version patches the backend many2one widget.
- It is specific to the sale order line product cell UI.
- Test in staging before production.
