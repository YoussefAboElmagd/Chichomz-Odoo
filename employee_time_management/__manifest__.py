# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Employee Time Management",
    "version": "1.0.0",
    "summary": "Track Employee Timeline",
    "author": "AO",
    "sequence": 1,
    "description": """Track Employee Timeline""",
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
        'security/ir.model.access.csv',
        'security/emp_security.xml',
        'security/ir_rule.xml',
        "views/break_view.xml",
        "views/idle_view.xml",
        "views/shift_management.xml",
        'views/project_task_timer_view.xml',
        'views/res_users_views.xml',
        "views/menu.xml",
        "views/ir_cron.xml",
    ],
    'assets': {
        'web.assets_backend': [
            '/employee_time_management/static/src/xml/systray.xml',
            'employee_time_management/static/src/xml/timer.xml',
            '/employee_time_management/static/src/css/systray.css',
            '/employee_time_management/static/src/js/systray.js',
            'employee_time_management/static/src/js/timer.js',
        ]
    },
    "demo": [],
    "installable": True,
    "auto_install": False,
}
