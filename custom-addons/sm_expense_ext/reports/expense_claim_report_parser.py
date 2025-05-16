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
from odoo import api, models, _



class ExpenseClaimReport(models.AbstractModel):
    _name = 'report.sm_expense_ext.expense_claim_template'
    _description = "Expense Claim Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.expense.sheet'].browse(docids[0])
        for rec in docs:
            expenses = []
            filtered = {}
            so_exist = False
            sm_exist = False
            for expense in rec.expense_line_ids:
                if expense.id not in expenses:
                    expenses.append(expense.product_id.id)
            for exp_id in expenses:
                filtered[exp_id] = rec.expense_line_ids.filtered(lambda exp: exp.product_id.id == exp_id)
            expense_line_ids = rec.expense_line_ids.filtered(lambda exp: exp.product_id.id == exp_id)
            if expense_line_ids:
                for expense_line_id in expense_line_ids:
                    if expense_line_id.so_id:
                        so_exist = True
                        break
                for expense_line_id in expense_line_ids:
                    if expense_line_id.salesman_id:
                        sm_exist = True
                        break
            docargs = {
                'doc_ids': docids,
                'doc_model': 'hr.expense.sheet',
                'docs': rec,
                'get_data': filtered,
                'so_exist':so_exist,
                'sm_exist':sm_exist,
            }
            return docargs
