# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2024 ZestyBeanz Technologies(<http://www.zbeanztech.com>)
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
    'name': 'Best ERP Customizations',
    'version': '18.0.0.6',
    'summary': 'Best ERP Customizations',
    'description': """
            Customizations for Best ERP Project.
    """,
    'category':'Purchase',
    'author': 'ZestyBeanz Technologies',
    'website': 'www.zbeanztech.com',
    'depends' : ['purchase', 'sale', 'account', 'sale_margin', 'stock'],
    'data': [
        'security/security.xml',		
		'views/purchase_view.xml',
		'views/sale_order_view.xml',
		'views/account_move_view.xml',
		'views/account_payment.xml',
		'views/stock_picking_view.xml',
        ],
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
