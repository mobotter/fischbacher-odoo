# Sale Input Barcode 19

Odoo 19 custom module for Odoo.sh.

## Purpose
Add products to sale orders by barcode scan. Each scan creates a new sale order line.

## Current scope
- Adds a "Scan Product" button to the sales order form
- Searches `product.product` by exact barcode
- Creates a new `sale.order.line` with quantity 1
- Rejects scan when no customer is selected
- Rejects unknown barcodes with a user error

## Intended platform
- Odoo.sh
- Odoo 19

## Installation on Odoo.sh
1. Put the module folder `sale_input_barcode_19` into your Git repository.
2. Push to your Odoo.sh branch.
3. Wait for the build to finish.
4. Update Apps List in Odoo.
5. Install **Sale Input Barcode 19**.

## Notes
- This is an MVP and should be validated in a staging branch first.
- Scanner should send barcode characters followed by `Enter`.
- Behavior is "always create a new line", not quantity increment.

## Suggested next improvements
- Dedicated OWL dialog for scan mode
- Optional setting: increment quantity instead of new line
- Better focus handling after each scan
- Support for product aliases/internal references
- Access rights and tests
