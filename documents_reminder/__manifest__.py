# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Documents Reminder',
    'version': '16.0.1.0.0',
    'summary': 'Documents Reminder',
    'description': '''A comprehensive module in Odoo designed to assist users in managing 
                    and staying up-to-date with their documents by providing reminders and 
                    organizational features for efficient document tracking and maintenance.''',
    'author': 'Dhvanil Trivedi',
    'maintainer': 'Dhvanil Trivedi',
    'category': 'Productivity',
    'depends': [
        'contacts','board', 'mail',
    ],
    'data': [
        'security/document_reminder_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/document_reminder_data.xml',
        'views/dashboard_views.xml',
        'views/document_reminder_views.xml',
        'views/document_reminder_type_views.xml',
        'views/document_reminder_tag_views.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'documents_reminder/static/src/js/lib/*',
            'documents_reminder/static/src/js/*',
            'documents_reminder/static/src/xml/**/*',
            'documents_reminder/static/src/scss/**/*',
        ],
    },
    'installable': True,
    'application': True,
}
