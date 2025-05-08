# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2025 ZestyBeanz Technologies(<http://www.zbeanztech.com>)
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
    "name": "ZB Salesperson Mapping.",
    "author": "ZestyBeanz Technologies",
    "version": "18.0.0.0.1",
    "description": """Map salesperson to sale order lines and journal entry lines.""",
    "summary": "This module allows tracking of salespersons on both Sale Order Lines and Journal Entry Lines.",
    "website": 'http://www.zbeanztech.com/',
    "category": "Sales",
    "depends": ['sale','account'],
    "data": [
        'views/account_move_view.xml',
        'views/sale_order_views.xml',
    ],
    "license": "LGPL-3",
    "auto_install": False,
    "installable": True,
    'application': True
}
