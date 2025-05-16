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
from odoo import fields, models,api,_
from odoo.exceptions import UserError

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    move_id = fields.Many2one('account.move', 'Entry')
    currency_rate = fields.Float(compute=False, default=1.00, digits=(12, 6))
    so_id = fields.Many2one('sale.order', 'Related Sale Order')
    salesman_id = fields.Many2one('res.users', 'Salesperson', default=lambda self: self.env.user)
    unit_amount = fields.Float("Unit Price", compute=False,precompute=False, readonly=False,required=True, copy=True,
        states={'done': [('readonly', True)]}, digits='Product Price')
    reference = fields.Text(string='Reference')
    
    def action_move_create(self):
        for ex in self:
            sub_total = ex.unit_amount * ex.quantity * ex.currency_rate
            sub_total = round(sub_total, 6)

            if int(sub_total) != int(ex.total_amount_company):
                raise UserError(_('Please recheck entered UNIT PRICE/CURRENCY/QUANTITY/RATE of your expense entry. \n'
                                  'Hint - line# : %s.', ex.name))
        res = super(HrExpense, self).action_move_create()
        for sheet in res:
            sheet_id = self.env['hr.expense.sheet'].browse(sheet)
            if sheet_id and res[sheet] and res[sheet].line_ids:

                for aml in res[sheet].line_ids:
                    if aml.expense_id:
                        if aml.expense_id.so_id:
                            aml.sale_order_id = aml.expense_id.so_id.id
                        if aml.expense_id.salesman_id:
                            aml.salesman_id = aml.expense_id.salesman_id.id
                            if aml.expense_id.salesman_id.department_id:
                                aml.department_id = aml.expense_id.salesman_id.department_id.id
                        # sm_stock_ext module dependency added, due to manufacturer_id field
                        if aml.expense_id.product_id and aml.expense_id.product_id.manufacturer_id:
                            aml.manufacturer_id = aml.expense_id.product_id.manufacturer_id.id
                        if aml.expense_id.unit_amount != 0:
                            if aml.expense_id.currency_id and self.env.user.company_id.currency_id:
                                if aml.expense_id.currency_id.id != self.env.user.company_id.currency_id.id:
                                    # foreign_to_base_curr = self.env.user.company_id.currency_id._compute(aml.expense_id.currency_id, 
                                    #                                                            self.env.user.company_id.currency_id,
                                    #                                                            aml.expense_id.unit_amount)
                                    foreign_to_base_curr = aml.expense_id.unit_amount * aml.expense_id.currency_rate
                                    aml.price_unit = foreign_to_base_curr
                if res[sheet]:
                    res[sheet].update({'ref': self.sheet_id.sequence_no,
                                       'payment_reference':self.sheet_id.sequence_no,})
        return res
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
               rec.name = rec.product_id.name
               
    @api.onchange('so_id')
    def onchange_so_id(self):
        for rec in self:
            salesman_ids = []
            if rec.so_id and rec.so_id.saleperson_ids:
                for saleperson_id in rec.so_id.saleperson_ids:
                    salesman_ids.append(saleperson_id.id)
                return {'domain':
                    {
                        'salesman_id': [('id', 'in', salesman_ids) or False]
                    }}
            elif not rec.so_id:
                salesman_ids = self.env['res.users'].search([]).ids
                return {'domain':
                    {
                        'salesman_id': [('id', 'in', salesman_ids)]
                    }}
    
    # This function overwrites _compute_amount function in hr_expense
    @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            taxes = expense._get_taxes(price=expense.unit_amount, quantity=expense.quantity)
            expense.total_amount = taxes['total_included']
            
    # This function overwrites _compute_is_editable in hr_expense       
    @api.depends('employee_id')
    def _compute_is_editable(self):
        is_account_manager = self.env.user.has_group('account.group_account_user') or self.env.user.has_group('account.group_account_manager')
        for expense in self:
            if expense.state == 'draft' or expense.sheet_id.state in ['draft']:
                expense.is_editable = True
            elif expense.sheet_id.state == 'approve':
                expense.is_editable = is_account_manager
            else:
                expense.is_editable = False 
            
            
            
            
