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
from odoo import fields,models,api,_
from odoo.exceptions import UserError,ValidationError

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'
    
    # @api.model_create_multi
    @api.model
    def create(self, vals):
        if vals.get('sequence_no', _('New')) == _('New'):
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet') or _('New')
        res = super(HrExpenseSheet, self).create(vals)
        if res.total_amount == 0:
            raise UserError(_('You cannot create a zero value expense. Please check the total amount!'))
        return res
    
    sequence_no = fields.Char(string='Sequence', 
                       default=lambda self: _('New'), 
                       copy=False, readonly=True)
    
    date = fields.Date('Bill Date')
    reference = fields.Text(string='Reference')
    
    #This function overwrites _compute_is_editable function in  base hr.expense.sheet
    @api.depends_context('uid')
    @api.depends('employee_id', 'user_id', 'state')
    def _compute_is_editable(self):
        is_manager = self.env.user.has_group('hr_expense.group_hr_expense_manager')
        is_approver = self.env.user.has_group('hr_expense.group_hr_expense_user')
        for report in self:
            # Employee can edit his own expense in draft only
            is_editable = (report.employee_id.user_id == self.env.user and report.state == 'draft') or (is_manager and report.state in ['draft', 'approve'])
            if not is_editable and report.state in ['draft', 'approve']:
                # expense manager also can't edit if state not in Draft
                current_managers = report.employee_id.expense_manager_id | report.employee_id.parent_id.user_id | report.employee_id.department_id.manager_id.user_id | report.user_id |report.employee_id.user_id.parent_user_id
                is_editable = (is_approver or self.env.user in current_managers) and report.employee_id.user_id != self.env.user and report.state == 'draft'
            report.is_editable = is_editable
    

    def action_expense_claim_report(self):
        if self.state == 'draft':
            raise ValidationError(_('The expense report is not in printable state. Expense is in %s' % (self.state)))
        return self.env.ref('sm_expense_ext.sm_expense_claim_report').report_action(self)
    
    """def action_submit_sheet(self):
        if not self.date:
            raise UserError(_('Please Enter Bill Date!'))

        for line in self.expense_line_ids:
            sub_total = line.unit_amount * line.quantity * line.currency_rate
            sub_total = round(sub_total, 6)

            if int(sub_total) != int(line.total_amount_company):
                raise UserError(_('Please recheck entered UNIT PRICE/CURRENCY/QUANTITY/RATE of your expense entry. \n'
                                  'Hint : line# %s.', line.name))

        res = super(HrExpenseSheet, self).action_submit_sheet()
        return res"""
        
   

    

   
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    