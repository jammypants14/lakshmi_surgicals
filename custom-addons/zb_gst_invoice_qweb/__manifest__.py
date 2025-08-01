#  -*- encoding: utf-8 -*-
#  OpenERP, Open Source Management Solution
#  Copyright (C) 2016 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>)
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

{
    'name': 'GST Invoice Print QWeb',
    'version': '18.0.0.21',
    'category': '',
    'summary': 'zb_gst_invoice_qweb',
    "license": "LGPL-3",
    'description': """
         This Module Print the Invoice & Credit Note in Indian GST Format
    """,
    'website': 'http://www.zbeanztech.com/',
    'Author': 'ZestyBeanz',
    'depends': ['account', 'base','l10n_in'],
    'qweb': [],
    'data': [
        'security/ir.model.access.csv',
        'report/reports.xml',
        'report/layout_templates.xml',
        'report/gst_invoice_qweb.xml',
        'report/original_copy_gst_invoice.xml',
        'wizards/custom_gst_invoice_views.xml',
        'views/account_move_views.xml',
        'views/res_company_views.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
