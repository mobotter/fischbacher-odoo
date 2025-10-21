# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.addons.zbsync.tests.test_pipe import ZBSPipelineCase
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestMapperOne(ZBSPipelineCase):
    pass
