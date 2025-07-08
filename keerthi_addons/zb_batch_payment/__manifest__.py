# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2025 ZestyBeanz Technologies.
#    (http://wwww.zbeanztech.com)
#    contact@zbeanztech.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Batch Payment',
    'version': '18.0.0.1',
    'summary': 'This module manages bank batch payment and report.',
    'description': """Bank batch payment and report""",
    'category': 'Accounting',
    'author': 'ZestyBeanz Technologies.',
    'website': 'www.zbeanztech.com',
    'depends': ['contacts','sale_management','hr','hr_expense','mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/batch_payment_views.xml',
        
    ],
    'assets': {

    },
    'test': [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}