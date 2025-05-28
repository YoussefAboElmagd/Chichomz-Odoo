# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Access Rights For Contacts And Shopify Orders",
    "version": "1.0.0",
    "summary": "Access Rights For Contacts And Shopify Orders",
    "author": "AO",
    "sequence": 1,
    "description": """Access Rights For Contacts And Shopify Orders""",
    "category": "Custom",
    "website": "https://www.odoo.com/page/billing",
    "license": "LGPL-3",
    "depends": [
        "base",
        "project",
        'sale',
        'hr'
    ],
    "data": [
        'security/groups.xml',
        'security/ir.model.access.csv',

    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
