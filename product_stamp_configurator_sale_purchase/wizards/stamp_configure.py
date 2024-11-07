from odoo import models
from odoo.tools import float_round

from ..const import DP_STAMP_SUPPLIER_PRICE


class StampConfigure(models.TransientModel):
    """Extend to integrate with stock."""

    _inherit = 'stamp.configure'

    def _prepare_mold_product(self):
        res = super()._prepare_mold_product()
        service_to_purchase = self.company_id.service_to_purchase_stamp
        if service_to_purchase:
            res['service_to_purchase'] = service_to_purchase
        return res

    def _prepare_common_product_vals(self, stamp_type):
        # TODO: add support to set `price` on product.supplierinfo
        # record. For this we will need to receive price_unit and cost
        # value in this method.
        res = super()._prepare_common_product_vals(stamp_type)
        partner_supplier = self.company_id.partner_supplier_default_stamp_id
        if partner_supplier:
            cost = self._get_supplier_cost(stamp_type)
            res['seller_ids'] = [
                (0, 0, {'partner_id': partner_supplier.id, 'price': cost})
            ]
        return res

    def _get_supplier_cost(self, stamp_type):
        self.ensure_one()
        digits = self.env['decimal.precision'].precision_get(DP_STAMP_SUPPLIER_PRICE)
        cost = getattr(self, f'cost_unit_{stamp_type}')
        return float_round(cost, precision_digits=digits)
