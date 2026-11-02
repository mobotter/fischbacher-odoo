# Copyright (c) 2026 Moritz Kern, Fischbacher GmbH + Co. KG
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

import logging

_logger = logging.getLogger(__name__)

#: Bisher per ID 234 bzw. Namenssuche verwendete Mengenstaffel-Preisliste.
LEGACY_PRICELIST_NAME = "Mengenstaffeln (EUR)"
LEGACY_PRICELIST_ID = 234

#: Standardpreisliste (Staffelpreise aus dem Produkt-Reiter "Preise").
DEFAULT_PRICELIST_ID = 1


def _find_legacy_quantity_pricelist(env):
    Pricelist = env["product.pricelist"].with_context(active_test=False)
    pricelist = Pricelist.search([("name", "=", LEGACY_PRICELIST_NAME)], limit=1)
    if not pricelist:
        candidate = Pricelist.browse(LEGACY_PRICELIST_ID).exists()
        if candidate and "mengenstaffel" in (candidate.name or "").lower():
            pricelist = candidate
    return pricelist


def mark_legacy_global_quantity_pricelist(env):
    """Markiert die Mengenstaffel-Preisliste (ersetzt die feste ID 234).

    Bereits markierte Preislisten werden nicht verändert.
    """
    pricelist = _find_legacy_quantity_pricelist(env)

    if not pricelist:
        _logger.warning(
            "Keine Preisliste '%s' gefunden. Bitte die Mengenstaffel-"
            "Preisliste manuell als 'Global berücksichtigen' markieren.",
            LEGACY_PRICELIST_NAME,
        )
        return

    if pricelist.is_global_quantity_pricelist:
        return

    pricelist.is_global_quantity_pricelist = True
    _logger.info(
        "Preisliste %s (ID %s) als globale Mengenstaffel markiert.",
        pricelist.name,
        pricelist.id,
    )


def mark_default_pricelist(env):
    """Markiert die Standardpreisliste (ID 1) als global zu berücksichtigen.

    Damit gelten die Staffelpreise aus dem Produkt-Reiter "Preise", die in
    dieser Preisliste liegen, auch bei Kunden mit anderer Preisliste.
    """
    pricelist = env["product.pricelist"].browse(DEFAULT_PRICELIST_ID).exists()
    if not pricelist or not pricelist.active:
        _logger.warning(
            "Standardpreisliste (ID %s) nicht gefunden. Bitte manuell als "
            "'Global berücksichtigen' markieren.",
            DEFAULT_PRICELIST_ID,
        )
        return

    if pricelist.is_global_quantity_pricelist:
        return

    pricelist.is_global_quantity_pricelist = True
    _logger.info(
        "Preisliste %s (ID %s) als global zu berücksichtigen markiert.",
        pricelist.name,
        pricelist.id,
    )


def post_init_hook(env):
    """Nur bei Neuinstallation: globale Preislisten markieren."""
    mark_legacy_global_quantity_pricelist(env)
    mark_default_pricelist(env)
