# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Notification Manager",
    "version": "1.0.0",
    "summary": "Control System Notifications",
    "author": "Ahmed Osama",
    "sequence": 1,
    "description": """Add Extra Features To Projects""",
    "category": "Custom",
    "website": "https://www.odoo.com/page/billing",
    "license": "LGPL-3",
    "depends": [
        "project",
    ],
    "data": [
        'security/ir.model.access.csv',
        "views/notification_view.xml",
    ],
   'assets':
        {
            'web.assets_backend': [
                'ao_notification/static/src/js/list_controller.js',
                'ao_notification/static/src/js/form_controller.js'
       ]},
    "demo": [],
    "installable": True,
    "auto_install": False,
}
