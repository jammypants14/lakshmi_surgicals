#  -*- encoding: utf-8 -*-
#  OpenERP, Open Source Management Solution
#  Copyright (C) 2025 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>)
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
    'name': 'GST Reports',
    'version': '18.0.0.0',
    'summary': 'GST Reports',
    'description': 'GST Reports',
    'category': '',
    'author': 'Zesty Beanz',
    'website': 'http://www.zbeanztech.com/',
    'license': 'LGPL-3',
    'depends': ['account', 'zb_gst_invoice_qweb'],
    'data': [
        'security/ir.model.access.csv',
        'security/access.xml',
        'views/account_journal_views.xml',
        'views/gst_report_views.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}