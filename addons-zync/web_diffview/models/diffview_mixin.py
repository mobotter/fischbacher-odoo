import os
import shutil
import tempfile
import uuid
from pathlib import Path
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import difflib


class DiffViewMixin(models.Model):
    _name = "mixin.diffview"
    _description = "Diff View Mixin"

    def _gitdiff(self, content1, content2):
        if not content1 or not content2:
            return ""
        text1_lines = content1.splitlines()
        text2_lines = content2.splitlines()
        html_diff = difflib.HtmlDiff()

        html_output = html_diff.make_file(
            text1_lines, text2_lines, fromdesc="Original", todesc="Modified"
        )
        return html_output
