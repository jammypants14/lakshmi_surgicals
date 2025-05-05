# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2024 ZestyBeanz Technologies
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

from odoo import api, fields, models, _

class Accountmove(models.Model):
    _inherit = "account.move"
    
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
    
class Accountmoveline(models.Model):
    _inherit = "account.move.line"
    
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account", related='move_id.analytic_account_id', store=True)
    
    def calculate_settled_till_data(self,date):
        debit_sum=credit_sum=0
        for rec in self:
            if rec.matched_debit_ids:
                for line in rec.matched_debit_ids:
                    if line.max_date <= from_date and line.max_date >= to_date:
                    
                        debit_sum+=line.debit_amount_currency
            if rec.matched_credit_ids:
                for line in rec.matched_credit_ids:
                    if line.max_date <= from_date and line.max_date >= to_date:
                        credit_sum+=line.credit_amount_currency
            
            settle=credit_sum - debit_sum
            return settle    