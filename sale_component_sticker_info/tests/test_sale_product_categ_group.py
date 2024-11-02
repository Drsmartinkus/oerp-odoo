from odoo.tests.common import TransactionCase


class TestSaleProductCategGroup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ResPartner = cls.env['res.partner']
        cls.ProductCategory = cls.env['product.category']
        cls.ProductProduct = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleOrderLine = cls.env['sale.order.line']
        cls.partner_1 = cls.ResPartner.create(
            {'name': 'MY-PARTNER-1', 'is_company': True}
        )
        cls.product_categ_all = cls.env.ref('product.product_category_all')
        cls.product_categ_a, cls.product_categ_b = cls.ProductCategory.create(
            [
                {
                    'name': 'C1',
                    'parent_id': cls.product_categ_all.id,
                    'property_group': 'A',
                },
                {
                    'name': 'C2',
                    'parent_id': cls.product_categ_all.id,
                    'property_group': 'B',
                },
            ]
        )
        cls.product_1_a, cls.product_2_a, cls.product_3_b = cls.ProductProduct.create(
            [
                {'name': 'P1-A', 'categ_id': cls.product_categ_a.id},
                {'name': 'P2-A', 'categ_id': cls.product_categ_a.id},
                {'name': 'P3-B', 'categ_id': cls.product_categ_b.id},
            ]
        )
        cls.sale_1 = cls.SaleOrder.create({'partner_id': cls.partner_1.id})

    def test_01_create_sale_product_categ_group(self):
        # WHEN
        line_1, line_2, line_3 = self.SaleOrderLine.create(
            [
                {'order_id': self.sale_1.id, 'product_id': self.product_1_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_2_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_3_b.id},
            ]
        )
        # THEN
        self.assertEqual(line_1.group_name, 'A-1')
        self.assertEqual(line_2.group_name, 'A-2')
        self.assertEqual(line_3.group_name, 'B-1')

    def test_02_create_sale_product_categ_group_multi_sale(self):
        # GIVEN
        sale_2 = self.SaleOrder.create({'partner_id': self.partner_1.id})
        # WHEN
        line_1, line_2, line_3, line_4, line_5, line_6 = self.SaleOrderLine.create(
            [
                {'order_id': self.sale_1.id, 'product_id': self.product_1_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_2_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_3_b.id},
                {'order_id': sale_2.id, 'product_id': self.product_1_a.id},
                {'order_id': sale_2.id, 'product_id': self.product_2_a.id},
                {'order_id': sale_2.id, 'product_id': self.product_3_b.id},
            ]
        )
        # THEN
        # Sale 1
        self.assertEqual(line_1.group_name, 'A-1')
        self.assertEqual(line_2.group_name, 'A-2')
        self.assertEqual(line_3.group_name, 'B-1')
        # Sale 2
        self.assertEqual(line_4.group_name, 'A-1')
        self.assertEqual(line_5.group_name, 'A-2')
        self.assertEqual(line_6.group_name, 'B-1')

    def test_03_write_sale_product_categ_group_multi_sale(self):
        # GIVEN
        sale_2 = self.SaleOrder.create({'partner_id': self.partner_1.id})
        line_1, line_2, line_3, line_4, line_5, line_6 = self.SaleOrderLine.create(
            [
                {'order_id': self.sale_1.id, 'product_id': self.product_1_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_2_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_3_b.id},
                {'order_id': sale_2.id, 'product_id': self.product_1_a.id},
                {'order_id': sale_2.id, 'product_id': self.product_2_a.id},
                {'order_id': sale_2.id, 'product_id': self.product_3_b.id},
            ]
        )
        # WHEN
        (line_1 | line_2 | line_3 | line_4 | line_5 | line_6).write(
            {'product_id': self.product_1_a}
        )
        # THEN
        # Sale 1
        self.assertEqual(line_1.group_name, 'A-1')
        self.assertEqual(line_2.group_name, 'A-2')
        self.assertEqual(line_3.group_name, 'A-3')
        # Sale 2
        self.assertEqual(line_4.group_name, 'A-1')
        self.assertEqual(line_5.group_name, 'A-2')
        self.assertEqual(line_6.group_name, 'A-3')

    def test_04_unlink_sale_product_categ_group(self):
        # WHEN
        line_1, line_2, line_3 = self.SaleOrderLine.create(
            [
                {'order_id': self.sale_1.id, 'product_id': self.product_2_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_1_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_3_b.id},
            ]
        )
        # THEN
        self.assertEqual(line_1.group_name, 'A-1')
        self.assertEqual(line_2.group_name, 'A-2')
        self.assertEqual(line_3.group_name, 'B-1')
        # WHEN
        line_1.unlink()
        self.assertFalse(line_1.exists())
        self.assertEqual(line_2.group_name, 'A-1')
        self.assertEqual(line_3.group_name, 'B-1')

    def test_05_unlink_sale_product_categ_group_multi(self):
        # GIVEN
        sale_2 = self.SaleOrder.create({'partner_id': self.partner_1.id})
        # WHEN
        line_1, line_2, line_3, line_4, line_5, line_6 = self.SaleOrderLine.create(
            [
                {'order_id': self.sale_1.id, 'product_id': self.product_2_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_1_a.id},
                {'order_id': self.sale_1.id, 'product_id': self.product_3_b.id},
                {'order_id': sale_2.id, 'product_id': self.product_1_a.id},
                {'order_id': sale_2.id, 'product_id': self.product_2_a.id},
                {'order_id': sale_2.id, 'product_id': self.product_3_b.id},
            ]
        )
        # THEN
        # Sale 1
        self.assertEqual(line_1.group_name, 'A-1')
        self.assertEqual(line_2.group_name, 'A-2')
        self.assertEqual(line_3.group_name, 'B-1')
        # Sale 2
        self.assertEqual(line_4.group_name, 'A-1')
        self.assertEqual(line_5.group_name, 'A-2')
        self.assertEqual(line_6.group_name, 'B-1')
        # WHEN
        (line_1 | line_4).unlink()
        self.assertFalse(line_1.exists())
        self.assertFalse(line_4.exists())
        self.assertEqual(line_2.group_name, 'A-1')
        self.assertEqual(line_3.group_name, 'B-1')
        self.assertEqual(line_5.group_name, 'A-1')
        self.assertEqual(line_6.group_name, 'B-1')
