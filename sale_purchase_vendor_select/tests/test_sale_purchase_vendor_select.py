from odoo.fields import Command

from odoo.addons.base.tests.common import BaseCommon


class TestSalePurchaseVendorSelect(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResPartner = cls.env['res.partner']
        cls.ProductProduct = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']
        cls.PurchaseOrder = cls.env['purchase.order']
        cls.ProductSupplierinfo = cls.env['product.supplierinfo']
        (
            cls.partner_1,
            cls.partner_vendor_1,
            cls.partner_vendor_2,
        ) = cls.ResPartner.create(
            [
                {'name': 'MY-PARTNER-1', 'is_company': True},
                {'name': 'MY-VENDOR-1', 'is_company': True},
                {'name': 'MY-VENDOR-2', 'is_company': True},
            ]
        )
        cls.stock_route_mto = cls.env.ref('stock.route_warehouse0_mto')
        cls.stock_route_mto.active = True
        cls.stock_route_buy = cls.env.ref('purchase_stock.route_warehouse0_buy')
        (cls.product_1, cls.product_2) = cls.ProductProduct.create(
            [
                {
                    'name': 'MY-PRODUCT-1',
                    'route_ids': [
                        (4, cls.stock_route_mto.id),
                        (4, cls.stock_route_buy.id),
                    ],
                },
                {
                    'name': 'MY-PRODUCT-2',
                    'route_ids': [
                        (4, cls.stock_route_mto.id),
                        (4, cls.stock_route_buy.id),
                    ],
                },
            ]
        )
        cls.sale_1 = cls.SaleOrder.create(
            {
                'partner_id': cls.partner_1.id,
                'order_line': [
                    Command.create(
                        {
                            'product_id': cls.product_1.id,
                            'product_uom_qty': 2,
                            'price_unit': 10,
                        }
                    ),
                    Command.create(
                        {
                            'product_id': cls.product_2.id,
                            'product_uom_qty': 2,
                            'price_unit': 20,
                        }
                    ),
                ],
            }
        )

    def test_01_sale_forced_vendor_match_both_products(self):
        # GIVEN
        self.sale_1.partner_supplier_id = self.partner_vendor_2.id
        self.product_1.seller_ids = [
            Command.create({'sequence': 5, 'partner_id': self.partner_vendor_1.id}),
            Command.create({'sequence': 10, 'partner_id': self.partner_vendor_2.id}),
        ]
        self.product_2.seller_ids = [
            Command.create({'sequence': 10, 'partner_id': self.partner_vendor_2.id}),
        ]
        # WHEN
        self.sale_1.action_confirm()
        # THEN
        self.assertFalse(
            self.PurchaseOrder.search([('partner_id', '=', self.partner_vendor_1.id)])
        )
        po = self.PurchaseOrder.search([('partner_id', '=', self.partner_vendor_2.id)])
        self.assertEqual(len(po), 1)
        self.assertEqual(len(po.order_line), 2)
        self.assertEqual(
            len(po.order_line.filtered(lambda r: r.product_id == self.product_1)), 1
        )
        self.assertEqual(
            len(po.order_line.filtered(lambda r: r.product_id == self.product_2)), 1
        )

    def test_02_sale_forced_vendor_match_single_product(self):
        # GIVEN
        self.sale_1.partner_supplier_id = self.partner_vendor_2.id
        self.product_1.seller_ids = [
            Command.create({'sequence': 5, 'partner_id': self.partner_vendor_1.id}),
            Command.create({'sequence': 10, 'partner_id': self.partner_vendor_2.id}),
        ]
        self.product_2.seller_ids = [
            Command.create({'sequence': 10, 'partner_id': self.partner_vendor_1.id}),
        ]
        # WHEN
        self.sale_1.action_confirm()
        # THEN
        po_1 = self.PurchaseOrder.search(
            [('partner_id', '=', self.partner_vendor_1.id)]
        )
        po_2 = self.PurchaseOrder.search(
            [('partner_id', '=', self.partner_vendor_2.id)]
        )
        self.assertEqual(len(po_1), 1)
        self.assertEqual(len(po_1.order_line), 1)
        self.assertEqual(
            len(po_1.order_line.filtered(lambda r: r.product_id == self.product_2)), 1
        )
        self.assertEqual(len(po_2), 1)
        self.assertEqual(len(po_2.order_line), 1)
        self.assertEqual(
            len(po_2.order_line.filtered(lambda r: r.product_id == self.product_1)), 1
        )

    def test_03_sale_not_forced_vendor(self):
        # GIVEN
        self.sale_1.partner_supplier_id = False
        self.product_1.seller_ids = [
            Command.create({'sequence': 5, 'partner_id': self.partner_vendor_1.id}),
            Command.create({'sequence': 10, 'partner_id': self.partner_vendor_2.id}),
        ]
        self.product_2.seller_ids = [
            Command.create({'sequence': 10, 'partner_id': self.partner_vendor_1.id}),
        ]
        # WHEN
        self.sale_1.action_confirm()
        # THEN
        self.assertFalse(
            self.PurchaseOrder.search([('partner_id', '=', self.partner_vendor_2.id)])
        )
        po = self.PurchaseOrder.search([('partner_id', '=', self.partner_vendor_1.id)])
        self.assertEqual(len(po), 1)
        self.assertEqual(len(po.order_line), 2)
        self.assertEqual(
            len(po.order_line.filtered(lambda r: r.product_id == self.product_1)), 1
        )
        self.assertEqual(
            len(po.order_line.filtered(lambda r: r.product_id == self.product_2)), 1
        )
