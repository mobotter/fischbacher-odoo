{
    "name": "Product Default Code Unique",
    "version": "19.0.1.0.0",
    "summary": "Ensures unique internal references for products.",
    "description": """
Ensures that the product internal reference (default_code) is unique.
Adds validation and related UI behavior for product records.
""",
    "category": "Inventory",
    "depends": ["product"],
    "author": "Moritz Kern",
    "license": "LGPL-3",
    "data": [
        "views/product_product_view.xml",
    ],
    "installable": True,
    "application": False,
}
