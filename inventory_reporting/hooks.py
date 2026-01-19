# Copyright 2023 Quartile Limited (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tools.sql import column_exists, create_column

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    if not column_exists(cr, "stock_valuation_layer", "report_category"):
        _logger.info("Creating column 'report_category' in stock_valuation_layer.")
        create_column(cr, "stock_valuation_layer", "report_category", "varchar")

    _logger.info("Setting report_category for SVL records with no stock move.")
    cr.execute(
        """
        UPDATE stock_valuation_layer
        SET report_category = 'price_update'
        WHERE report_category IS NULL
        AND stock_move_id IS NULL
        """
    )

    _logger.info("Setting report_category for non-product SVL records.")
    cr.execute(
        """
        UPDATE stock_valuation_layer svl
        SET report_category = CASE
            WHEN spt.code = 'incoming' THEN 'receipt'
            WHEN spt.code = 'outgoing' THEN 'vendor_return'
            ELSE 'non_product'
        END
        FROM stock_move sm
        LEFT JOIN stock_picking_type spt ON spt.id = sm.picking_type_id
        JOIN product_product pp ON pp.id = svl.product_id
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE svl.report_category IS NULL
        AND svl.stock_move_id = sm.id
        AND pt.detailed_type != 'product'
        """
    )

    _logger.info("Setting report_category for product SVL records.")
    cr.execute(
        """
        WITH matches AS (
            SELECT
                svl.id,
                CASE
                    WHEN sm.picking_code = 'incoming'
                        AND sm.origin_returned_move_id IS NULL
                        AND sm.unbuild_id IS NULL
                    THEN 1 ELSE 0
                END AS receipt,
                CASE
                    WHEN sm.picking_code = 'outgoing'
                        AND sm.origin_returned_move_id IS NOT NULL
                    THEN 1 ELSE 0
                END AS vendor_return,
                CASE
                    WHEN dest.usage = 'production'
                        AND COALESCE(loc.is_subcontracting_location, FALSE) = FALSE
                        AND sm.origin_returned_move_id IS NULL
                        AND sm.picking_code IN ('internal', 'outgoing')
                        AND sm.unbuild_id IS NULL
                    THEN 1 ELSE 0
                END AS component_flush,
                CASE
                    WHEN COALESCE(dest.is_subcontracting_location, FALSE) = FALSE
                        AND loc.usage = 'production'
                        AND sm.unbuild_id IS NULL
                    THEN 1 ELSE 0
                END AS component_return,
                CASE
                    WHEN (loc.usage = 'inventory' OR dest.usage = 'inventory')
                        AND sm.scrapped = FALSE
                        AND sm.unbuild_id IS NULL
                    THEN 1 ELSE 0
                END AS inventory_adjustment,
                CASE
                    WHEN sm.scrapped = TRUE
                    THEN 1 ELSE 0
                END AS scrap,
                CASE
                    WHEN (
                        (COALESCE(dest.is_subcontracting_location, FALSE) = TRUE
                            AND loc.usage != 'inventory')
                        OR (COALESCE(loc.is_subcontracting_location, FALSE) = TRUE
                            AND dest.usage != 'inventory')
                    )
                        AND sm.scrapped = FALSE
                        AND sm.unbuild_id IS NULL
                    THEN 1 ELSE 0
                END AS subcontracting,
                CASE
                    WHEN sm.unbuild_id IS NOT NULL
                    THEN 1 ELSE 0
                END AS unbuild,
                (
                    CASE
                        WHEN sm.picking_code = 'incoming'
                            AND sm.origin_returned_move_id IS NULL
                            AND sm.unbuild_id IS NULL
                        THEN 1 ELSE 0
                    END
                    + CASE
                        WHEN sm.picking_code = 'outgoing'
                            AND sm.origin_returned_move_id IS NOT NULL
                        THEN 1 ELSE 0
                    END
                    + CASE
                        WHEN dest.usage = 'production'
                            AND COALESCE(loc.is_subcontracting_location, FALSE) = FALSE
                            AND sm.origin_returned_move_id IS NULL
                            AND sm.picking_code IN ('internal', 'outgoing')
                            AND sm.unbuild_id IS NULL
                        THEN 1 ELSE 0
                    END
                    + CASE
                        WHEN COALESCE(dest.is_subcontracting_location, FALSE) = FALSE
                            AND loc.usage = 'production'
                            AND sm.unbuild_id IS NULL
                        THEN 1 ELSE 0
                    END
                    + CASE
                        WHEN (loc.usage = 'inventory' OR dest.usage = 'inventory')
                            AND sm.scrapped = FALSE
                            AND sm.unbuild_id IS NULL
                        THEN 1 ELSE 0
                    END
                    + CASE
                        WHEN sm.scrapped = TRUE
                        THEN 1 ELSE 0
                    END
                    + CASE
                        WHEN (
                            (COALESCE(dest.is_subcontracting_location, FALSE) = TRUE
                                AND loc.usage != 'inventory')
                            OR (COALESCE(loc.is_subcontracting_location, FALSE) = TRUE
                                AND dest.usage != 'inventory')
                        )
                            AND sm.scrapped = FALSE
                            AND sm.unbuild_id IS NULL
                        THEN 1 ELSE 0
                    END
                    + CASE
                        WHEN sm.unbuild_id IS NOT NULL
                        THEN 1 ELSE 0
                    END
                ) AS match_count
            FROM stock_valuation_layer svl
            JOIN stock_move sm ON sm.id = svl.stock_move_id
            JOIN product_product pp ON pp.id = svl.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN stock_location loc ON loc.id = sm.location_id
            LEFT JOIN stock_location dest ON dest.id = sm.location_dest_id
            WHERE svl.report_category IS NULL
            AND pt.detailed_type = 'product'
        )
        UPDATE stock_valuation_layer svl
        SET report_category = CASE
            WHEN m.match_count = 1 THEN
                CASE
                    WHEN m.receipt = 1 THEN 'receipt'
                    WHEN m.vendor_return = 1 THEN 'vendor_return'
                    WHEN m.component_flush = 1 THEN 'component_flush'
                    WHEN m.component_return = 1 THEN 'component_return'
                    WHEN m.inventory_adjustment = 1 THEN 'inventory_adjustment'
                    WHEN m.scrap = 1 THEN 'scrap'
                    WHEN m.subcontracting = 1 THEN 'subcontracting'
                    WHEN m.unbuild = 1 THEN 'unbuild'
                    ELSE 'other'
                END
            ELSE 'other'
        END
        FROM matches m
        WHERE svl.id = m.id
        """
    )

    _logger.info("Setting report_category to 'other' for remaining SVL records.")
    cr.execute(
        """
        UPDATE stock_valuation_layer
        SET report_category = 'other'
        WHERE report_category IS NULL
        """
    )
