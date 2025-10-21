# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).


def migrate(cr, version):
    env.cr.execute(
        """
    update zbs_grabber_file
    set filepath = filepath || coalesce(glob, '')
    """
    )
