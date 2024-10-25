# Author: Andrius Laukavičius. Copyright: Andrius Laukavičius.
# See LICENSE and COPYRIGHT files for details.
{
    "name": "Purchase - No Vendor Grouping",
    "version": "17.0.1.0.0",
    "summary": "Do not group purchase order procurements via vendors",
    "license": "LGPL-3",
    "author": "Andrius Laukavičius",
    "website": "https://timefordev.com",
    "category": "Inventory/Purchase",
    "depends": [
        # odoo
        "purchase_stock",
    ],
    "installable": True,
    "data": ["views/res_config_settings.xml"],
}
