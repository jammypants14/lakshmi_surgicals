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
    "name": "Lakshmi Surgicals Customizations ",
    "summary": "Lakshmi Surgicals Customizations",
    "version": "18.0.0.22",
    "category": "Accounting",
    "website": "http://www.zbeanztech.com/",
    "description": """
        Lakshmi Surgicals Customizations
    """,
    'images':[
    
    ],
    "author": "ZestyBeanz Technologies",
    "license": "LGPL-3",
    "depends": ['zb_gst_invoice_qweb', 'account', 'purchase'],
    "data": [
        'report/invoice_report.xml',
        'report/report.xml',
        'report/external_layout.xml',
        'report/purchase_order_print.xml',
        'report/po_print_base_value_only.xml',
        'report/print_service_order.xml',
        'report/gst_invoice_qweb.xml',
        'report/sale_order_print.xml',
        'report/stock_reports.xml',
        'views/account_move_view.xml',
        'views/sale_order_view.xml',
        'views/res_users_view.xml',
        'views/purchase_order_view.xml',
        'views/stock_picking.xml',
        
        
        
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    
   

}
