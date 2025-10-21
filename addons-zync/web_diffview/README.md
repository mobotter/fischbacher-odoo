#1 web_diffview


## How to use

### Python
```
class Partner(models.Model):
  _inherit = ['mixin.diffview', 'res.partner']
  _name = 'res.partner'

  diffcontent = fields.Text(compute="_compute_diffcontent")

  def _compute_diffcontent(self):
	for rec in self:
	  rec.diffcontent = rec._gitdiff("a", "b")
```

### XML Form

<field name="diffcontent" widget="diff_view"/>



#2 Contributors

* Marc Wimmer <marc@itewimmer.de>

