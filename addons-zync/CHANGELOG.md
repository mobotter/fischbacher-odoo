# 2025-05

- switching from outdated pymssql to python-tds - compatiability with debian packages

# 2025-04

- BREAKING: renamed following functions to just "\_as_python_object()" in zebrooset from

  - _as_json_
  - \_as_python_type
  - \_as_plain_python
  - \_get_python_type

  Affected: perhaps local created python transformers / code snippets

# 2025-03

- BREAKING: file grabber: just one expression for folders; recursive expression is extra

# 2024-07

- BREAKING: button after success turned from json to python

# BREAKING: fileupload dialog and buttons - delete existing data

# 2024-06

- change the code in cronjobs to start with .start() --> .start(data=None, manual=False)
- BREAKING: xml2dict - result in content

# 2024-01

- deleting all mappings: making a json snapshot before
- BREAKING: mapping: browse objects (local ones or rpc remote objects) of odoo now export many2one fields in direct mappings as int/False instead of lists

# 2023-10-12

**_ Breaking Change - Triggers _**

- Web Worker looses data!!!!!
- Triggers are lost!
