# -*- coding: utf-8 -*-
{
    'name': 'Odoo Shopify Connector',
    'version': '16.0.10',
    'category': 'Services',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'www.pragtech.co.in',
    'summary': 'This module is used to connect odoo with shopify',
    'description': """
       Odoo-shopify connector: This module is used to connect odoo with shopify.
    """,
    'depends': ['base', 'sale', 'sale_management', 'product', 'stock', 'delivery'],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'wizard/shopify_operation_view.xml',
        'wizard/export_customer_shopify_view.xml',
        'wizard/export_products_shopify_view.xml',
        'wizard/export_order_shopify_view.xml',
        'views/shopify_instance_view.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml',
        'views/order_view.xml',
        'views/shopify_product_image_view.xml',
        'views/shopify_location_view.xml',
        'views/gift_card_view.xml',
        'views/payout_view.xml',
        'views/menu_view.xml',
    ],
    'images': ['static/description/shopify_connector_app.gif'],
    'live_test_url': 'https://www.pragtech.co.in/company/proposal-form.html?id=103&name=Odoo-Shopify-Connector',
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
}
