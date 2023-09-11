# Copyright 2023 Quartile Limited
{
    "name": "Product PLM Import",
    "version": "16.0.1.0.0",
    "category": "Stock",
    "license": "Other proprietary",
    "author": "Quartile Limited",
    "website": "https://www.quartile.co",
    "depends": [
        "purchase_stock",
        "product_lot_sequence",  # lot_sequence_padding, lot_sequence_prefix
        "stock_picking_auto_create_lot",  # auto_create_lot
        "base_data_import",
        "product_alternative_code",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/ir_cron_data.xml",
        "data/menu_item_data.xml",
        "views/data_import_log_views.xml",
        "views/plm_category_views.xml",
        "views/plm_item_type_views.xml",
        "views/plm_procure_flag_views.xml",
        "views/plm_product_mapping_views.xml",
        "views/product_plm_views.xml",
        "views/product_template_views.xml",
        "views/res_company_views.xml",
        "wizards/product_plm_import_views.xml",
    ],
    "installable": True,
}
