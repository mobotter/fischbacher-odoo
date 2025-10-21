# How to use

Exports a flow and including mappings.
Replaces flow on destination system.

```python
fields:


fields.XXXX(xport_ignore=True)  - to leave out field
fields.XXXX(xport_rule='use_existing') - ?please documentation?
fields.XXXX(xport_rule='by_name')  - at many2one: to lookup many2one record by name in source and destination
fields.XXXX(xport_rule='custom', xport_export='function string name', xport_import='function string name')

    @api.model
    def export_data(self, value):
        return {
        }

    @api.model
    def import_data(self, value):
        self.search ....
        return field_value to set

```

## Authors

- Marc Wimmer <marc@zebroo.de>
