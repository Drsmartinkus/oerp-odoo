from odoo.addons.base.tests.common import BaseCommon


class TestSalePurchaseVendorSelectMrp(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResPartner = cls.env['res.partner']
        cls.ProductProduct = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']
        cls.MrpProduction = cls.env['mrp.production']
        cls.MrpBom = cls.env['mrp.bom']
        cls.stock_route_manufacture = cls.env.ref('mrp.route_warehouse0_manufacture')
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
        (
            cls.product_main,
            cls.product_comp,
            cls.product_sub_comp,
            cls.product_sub_comp_raw,
            cls.product_raw,
        ) = cls.ProductProduct.create(
            [
                {
                    'name': 'MY-MAIN-PRODUCT',
                    'route_ids': [
                        (4, cls.stock_route_mto.id),
                        (4, cls.stock_route_manufacture.id),
                    ],
                },
                # Needed to make main product
                {
                    'name': 'MY-COMPONENT',
                    'route_ids': [
                        (4, cls.stock_route_mto.id),
                        (4, cls.stock_route_manufacture.id),
                    ],
                },
                # Needed to make component.
                {
                    'name': 'MY-SUB-COMPONENT',
                    'route_ids': [
                        (4, cls.stock_route_mto.id),
                        (4, cls.stock_route_manufacture.id),
                    ],
                },
                # Sub component, but bought
                {
                    'name': 'MY-SUB-COMPONENT-RAW',
                    'route_ids': [
                        (4, cls.stock_route_mto.id),
                        (4, cls.stock_route_buy.id),
                    ],
                },
                {
                    'name': 'MY-RAW-MATERIAL',
                    'route_ids': [
                        (4, cls.stock_route_mto.id),
                        (4, cls.stock_route_buy.id),
                    ],
                },
            ]
        )
        cls.MrpBom.create(
            [
                {
                    'product_tmpl_id': cls.product_main.product_tmpl_id.id,
                    'bom_line_ids': [(0, 0, {'product_id': cls.product_comp.id})],
                },
                {
                    'product_tmpl_id': cls.product_comp.product_tmpl_id.id,
                    'bom_line_ids': [
                        (0, 0, {'product_id': cls.product_sub_comp.id}),
                        (0, 0, {'product_id': cls.product_sub_comp_raw.id}),
                    ],
                },
                {
                    'product_tmpl_id': cls.product_sub_comp.product_tmpl_id.id,
                    'bom_line_ids': [(0, 0, {'product_id': cls.product_raw.id})],
                },
            ]
        )
        cls.sale_1 = cls.SaleOrder.create(
            {
                'partner_id': cls.partner_1.id,
                'order_line': [
                    (
                        0,
                        0,
                        {
                            'product_id': cls.product_main.id,
                            'product_uom_qty': 2,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            'product_id': cls.product_main.id,
                            'product_uom_qty': 1,
                        },
                    ),
                ],
            }
        )

    def test_01_sale_mrp_forced_vendor_match_both_products(self):
        # GIVEN
        self.sale_1.partner_supplier_id = self.partner_vendor_2.id
        (self.product_sub_comp_raw | self.product_raw).seller_ids = [
            (0, 0, {'sequence': 5, 'partner_id': self.partner_vendor_1.id}),
            (0, 0, {'sequence': 7, 'partner_id': self.partner_vendor_2.id}),
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
            len(
                po.order_line.filtered(
                    lambda r: r.product_id == self.product_sub_comp_raw
                )
            ),
            1,
        )
        self.assertEqual(
            len(po.order_line.filtered(lambda r: r.product_id == self.product_raw)), 1
        )

    def test_02_sale_mrp_forced_vendor_match_single_product(self):
        # GIVEN
        self.sale_1.partner_supplier_id = self.partner_vendor_2.id
        self.product_sub_comp_raw.seller_ids = [
            (0, 0, {'sequence': 5, 'partner_id': self.partner_vendor_1.id}),
            (0, 0, {'sequence': 7, 'partner_id': self.partner_vendor_2.id}),
        ]
        self.product_raw.seller_ids = [
            (0, 0, {'sequence': 5, 'partner_id': self.partner_vendor_1.id}),
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
            len(po_1.order_line.filtered(lambda r: r.product_id == self.product_raw)), 1
        )
        self.assertEqual(len(po_2), 1)
        self.assertEqual(len(po_2.order_line), 1)
        self.assertEqual(
            len(
                po_2.order_line.filtered(
                    lambda r: r.product_id == self.product_sub_comp_raw
                )
            ),
            1,
        )

    def test_03_sale_mrp_not_forced_vendor(self):
        # GIVEN
        self.sale_1.partner_supplier_id = False
        (self.product_sub_comp_raw | self.product_raw).seller_ids = [
            (0, 0, {'sequence': 5, 'partner_id': self.partner_vendor_1.id}),
            (0, 0, {'sequence': 7, 'partner_id': self.partner_vendor_2.id}),
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
            len(
                po.order_line.filtered(
                    lambda r: r.product_id == self.product_sub_comp_raw
                )
            ),
            1,
        )
        self.assertEqual(
            len(po.order_line.filtered(lambda r: r.product_id == self.product_raw)), 1
        )
