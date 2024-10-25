from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        if self.env.company.purchase_no_vendor_grouping:
            # To have a domain that will not find any match!
            domain += (('id', '=', 0),)
        return domain
