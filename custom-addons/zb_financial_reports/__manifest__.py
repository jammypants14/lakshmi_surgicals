# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2023 ZestyBeanz Technologies(<http://www.zbeanztech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Financial Reports',
    'version': '18.0.0.26',
    'summary': 'This Module Manages various Financial Reports',
    'description': """ This Module Manages various Ledger Reports.
    """,
    'category':'Accounting',
    'author': ' ZestyBeanz Technologies',
    'website': 'www.zbeanztech.com',
    "license": "LGPL-3",
    'depends': ['account','base'],
    'data': [
        'security/ir.model.access.csv',
        'reports/reports.xml',
        'reports/balance_confirmation_report.xml',
        'reports/partner_summary_report.xml',
        'reports/ageing_report_qweb.xml',
        'wizards/day_book_views.xml',
        'wizards/general_ledger_wiz_view.xml',
        'wizards/partner_ledger_wiz_view.xml',
        'wizards/trial_balance_wiz_view.xml',
        'wizards/partner_summary_wiz_view.xml',
        'wizards/ageing_report_wizard_view.xml',
        # 'wizards/menu.xml',
        'wizards/partner_ledger_report_wiz_view.xml',
        'wizards/balance_confirmation_view.xml',
        'views/partner_ledger_view.xml',
        'views/res_partner_views.xml',
        'wizards/menu.xml',
        ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
