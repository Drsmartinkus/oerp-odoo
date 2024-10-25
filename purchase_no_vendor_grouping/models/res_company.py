from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    purchase_no_vendor_grouping = fields.Boolean(
        "No Vendor Grouping for Purchases",
    )
