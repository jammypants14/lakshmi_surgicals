# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2022 Sedeer Medical LLC.
#    (https://wwww.sedeer.com)
#    Contact : it@sedeer.com
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
    'name': 'Expense Extension',
    'version': '18.0.0.0.0',
    'category': 'Expense',
    'summary': 'This Module manages customisation for Expense',
    'description': """
    This Module manages customisation for Expense
    """,
    'author': 'Zesty Beanz Technologies Pvt. Ltd',
    'license': "LGPL-3",
    'website': 'www.zbeanztech.com',
    'depends': ['hr_expense', 'sale_expense'],
    'data': [
        'data/ir_sequence_data.xml',
        #'security/ir.model.access.csv',
        #'security/expense_security.xml',
        'reports/reports.xml',
        'reports/expense_claim_report.xml',
        'reports/training_expense_claim_report.xml',
        'views/hr_expense_sheet_view.xml',
        ],
    'test':  [],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
