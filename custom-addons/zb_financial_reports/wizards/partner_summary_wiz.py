# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2023 ZestyBeanz Technologies
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
import io
from _datetime import datetime,date
from datetime import timedelta
import base64

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
from odoo import fields, models,api,_
from odoo.exceptions import ValidationError,UserError

class PartnerSummaryWizard(models.TransientModel):

    _name = 'partner.summary.wiz'
    _description = 'Partner Summary Wizard'
    
    
    def _get_default_accounts(self):
        for rec in self:
            if rec.account_type:
                account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
                return account_ids.ids
            
    name = fields.Char('Name',default = 'Partner Summary')
    partner_summary_line_ids = fields.One2many('partner.summary.wiz.line', 'partner_summary_id', string='Partner Summary Wizard Lines')
    from_date = fields.Date('From Date',default=lambda self: date.today() - timedelta(days=30))
    to_date = fields.Date('To Date',default=fields.Date.context_today)
    account_type = fields.Selection([('asset_receivable','Receivable'),('liability_payable','Payable'),('receivable_payable','Receivable & Payable')])
    account_ids = fields.Many2many('account.account','partner_summ_account_rel','partner_summ_id','acc_id','Account(s)')
    partner_ids = fields.Many2many('res.partner','part_summ_partner_rel','part_summ_vend_id','summ_part_id','Partner(s)')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    label = fields.Char("Label")
    group_by = fields.Selection([('partner','Partner')],default='partner')
    
    # currency_id = fields.Many2one('res.currency',string='Currency')
    company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    # amount = fields.Monetary(string='Amount', currency_field='company_currency_id')
    show_draft = fields.Boolean(string='Show Draft Also')
    show_partner = fields.Boolean('Show Partner')
    partner_tag_ids = fields.Many2many('res.partner.category','part_cat_tag_rel','part_categ_vendor_id','tag_vend_id',string='Partner Tag(s)')
    customers_for_the_period = fields.Boolean(string='Customers for the Period')   
    company_id=fields.Many2one("res.company", default=lambda self: self.env.company.id)
    child_company_ids=fields.Many2many("res.company","company_partner_summary_rel","company_id","partner_summary_id",string="Child Company") 
    
    
    @api.onchange('company_id')  
    def onchange_company_id(self):
        for rec in self:
            list1=[(5,0,0)] 
            for child in rec.company_id.child_ids:
                list1.append(child)                       
            rec.child_company_ids=[(6,0,rec.company_id.child_ids.ids)]  
    
    @api.onchange('partner_tag_ids')
    def onchange_partner_tag_ids(self):
        for rec in self:
            if rec.partner_tag_ids:
                rec.show_partner = True
                new_partner_ids = rec.partner_tag_ids.mapped('partner_ids').ids
                rec.partner_ids = [(6, 0, new_partner_ids)]
            else:
                rec.partner_ids = [(6, 0, [])]
                rec.show_partner = False
    
    
    @api.onchange('account_type')
    def onchange_account_type(self):
        for rec in self:
            if rec.account_type:
                if rec.account_type == 'asset_receivable':
                    account_ids = self.env['account.account'].search([('account_type','=','asset_receivable')])
                elif rec.account_type == 'liability_payable':
                    account_ids = self.env['account.account'].search([('account_type','=','liability_payable')])
                elif rec.account_type == 'receivable_payable':
                    account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
            # else:
            #     account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
            
                rec.account_ids = [(6,0,account_ids.ids)]
        
    # def load_data(self):
    #
    #     for rec in self:
    #         rec.partner_summary_line_ids = False
    #         if rec.show_draft == True:
    #             domain = [('parent_state','in',['posted','draft'])]
    #         else:
    #             domain = [('parent_state', '=', 'posted')]
    #         # if rec.from_date:
    #         #     domain.append(('date','>=',rec.from_date))
    #         if self.env.company:
    #             company_ids = self.env['res.company'].search([('parent_id','=',self.env.company.id)])
    #             if company_ids:
    #                 domain.append('|')
    #                 domain.append(('company_id','=',self.env.company.id))
    #                 domain.append(('company_id','in',company_ids.ids))
    #             else:
    #                 domain.append(('company_id','=',self.env.company.id))
    #         # if rec.to_date:
    #         #     domain.append(('date','<=',rec.to_date))
    #         if rec.analytic_account_id:
    #             domain.append(('analytic_account_id','=',rec.analytic_account_id.id))
    #         if rec.account_ids:
    #             domain.append(('account_id','in',rec.account_ids.ids))
    #         if rec.account_type:
    #             if rec.account_type == 'asset_receivable':
    #                 domain.append(('account_type','=','asset_receivable'))
    #             elif rec.account_type == 'liability_payable':
    #                 domain.append(('account_type','=','liability_payable'))
    #             elif rec.account_type == 'receivable_payable':
    #                 domain.append(('account_type','in',['asset_receivable','liability_payable']))
    #         else:
    #             domain.append(('account_type','in',['asset_receivable','liability_payable']))
    #         if rec.partner_ids:
    #             domain.append(('partner_id','in',rec.partner_ids.ids))
    #         partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
    #
    #         line_list = []
    #
    #         for partner in partner_ids:
    #             domain = [('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted'),('account_type','in',['asset_receivable','liability_payable'])]
    #             if rec.account_ids:
    #                 domain.append(('account_id','in',rec.account_ids.ids))
    #
    #             opening_balance = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted')]).mapped('debit')) - sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted')]).mapped('credit'))
    #
    #             domain = [('partner_id','=',partner.id),('date','>=',rec.to_date),('parent_state','=','posted'),('account_type','in',['asset_receivable','liability_payable'])]
    #             if rec.account_ids:
    #                 domain.append(('account_id','in',rec.account_ids.ids))
    #             if rec.to_date:
    #                 domain.append(('date','<=',rec.to_date))
    #
    #             debit = sum(self.env['account.move.line'].search(domain).mapped('debit'))
    #             credit = sum(self.env['account.move.line'].search(domain).mapped('credit'))
    #
    #
    #             closing_balance = opening_balance + (debit - credit)
    #             print("=================closing_balance=============================",closing_balance)
    #             print("====================debit====================",debit)
    #             print("====================credit====================",credit)
    #             print("=============closing_balance,closing_balance=======================",opening_balance)
    #
    #             balance_currency = sum(self.env['account.move.line'].search(domain).mapped('amount_currency'))
    #
    #
    #             # line_list.append((0, 0, {'name':partner.display_name,'ref':'Opening Balance','balance':opening_balance,'balance_currency':opening_balance_currency}))
    #             # for line in line_ids:
    #             # if line.partner_id == partner:
    #             vals = {
    #                 # 'move_line_id': line.move_line_id.id,
    #                         # 'date': line.date,
    #                         # 'ref': line.move_id.name,
    #                         # 'label': line.name,
    #                         'name': partner.display_name,
    #                         'partner_id': partner.id,
    #                         # 'analytic_account_id': line.analytic_account_id.id,
    #                         # 'amount_currency': line.amount_currency,
    #                         # 'currency_id': line.currency_id.id,
    #
    #                         'debit': debit,
    #                         'credit': credit,
    #                         'opening_balance': opening_balance,
    #                         'closing_balance' : closing_balance,
    #                         'balance_currency' : balance_currency
    #
    #                         }
    #             line_list.append((0, 0, vals))
    #                 # opening_balance = opening_balance + (line.debit-line.credit)
    #                 # opening_balance_currency = opening_balance_currency + line.amount_currency
    #
    #
    #
    #
    #         rec.partner_summary_line_ids = line_list
    def load_data(self):
        for rec in self:
            rec.partner_summary_line_ids = False
            
            # Set the domain based on conditions
            if rec.show_draft:
                domain = [('parent_state', 'in', ['posted', 'draft'])]
            else:
                domain = [('parent_state', '=', 'posted')]
    
            # if self.env.user.has_group('account.group_account_manager'): 
            #     if self.env.company:
            #         company_ids = self.env['res.company'].search([('parent_id', '=', self.env.company.parent_id.id)])
            #         if company_ids:
            #             domain.append('|')
            #             domain.append(('company_id', '=', self.env.company.id))
            #             domain.append(('company_id', 'in', company_ids.ids))
            #         else:
            #             domain.append(('company_id', '=', self.env.company.id))
            # else:
            #     domain.append(('company_id', '=', self.env.company.id))
            company_ids = self.env.context.get('allowed_company_ids',[])
            if self.env.user.has_group('account.group_account_manager'):
                if company_ids:
                    # domain.append('|')
                    domain.append(('company_id','in',company_ids))
                else:
                    domain.append(('company_id','=',rec.company_id.id))
            else:
                domain.append(('company_id','=',rec.company_id.id))     
            
            if rec.analytic_account_id:
                domain.append(('analytic_account_id', '=', rec.analytic_account_id.id))
            if rec.account_ids:
                domain.append(('account_id', 'in', rec.account_ids.ids))
            if rec.account_type:
                if rec.account_type == 'asset_receivable':
                    domain.append(('account_type', '=', 'asset_receivable'))
                elif rec.account_type == 'liability_payable':
                    domain.append(('account_type', '=', 'liability_payable'))
                elif rec.account_type == 'receivable_payable':
                    domain.append(('account_type', 'in', ['asset_receivable', 'liability_payable']))
            else:
                domain.append(('account_type', 'in', ['asset_receivable', 'liability_payable']))
            
            if rec.partner_ids:
                domain.append(('partner_id', 'in', rec.partner_ids.ids))
            
            # Get unique partners
            partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
            
            line_list = []
            
            for partner in partner_ids:
                # Opening balance calculation
                if self.env.user.has_group('account.group_account_manager'):
                    company_filter = []
                else:
                    company_filter = [('company_id', '=', self.env.company.id)]
                    
                opening_domain = [
                    ('partner_id', '=', partner.id),
                    ('date', '<', rec.from_date),
                    ('parent_state', '=', 'posted'),
                    ('account_type', 'in', ['asset_receivable', 'liability_payable'])
                ] + company_filter
                if rec.account_ids:
                    opening_domain.append(('account_id', 'in', rec.account_ids.ids))
                    
                opening_balance = sum(self.env['account.move.line'].search(opening_domain).mapped('debit')) - \
                                  sum(self.env['account.move.line'].search(opening_domain).mapped('credit'))
                
                # Lines within the date range to calculate cumulative balance
                transaction_domain = [
                    ('partner_id', '=', partner.id),
                    ('date', '>=', rec.from_date),
                    ('date', '<=', rec.to_date),
                    ('parent_state', '=', 'posted'),
                    ('account_type', 'in', ['asset_receivable', 'liability_payable'])
                ] + company_filter
                if rec.account_ids:
                    transaction_domain.append(('account_id', 'in', rec.account_ids.ids))
                
                lines = self.env['account.move.line'].search(transaction_domain, order="date asc")
                
                # Calculate cumulative balance
                cumulative_balance = opening_balance
                total_debit = sum(line.debit for line in lines)
                total_credit = sum(line.credit for line in lines)
                for line in lines:
                    # Update cumulative balance
                    cumulative_balance += line.debit - line.credit
    
                
                if not (opening_balance or total_debit or total_credit or cumulative_balance):
                    continue
                # Summarize the results for each partner
                
                if rec.customers_for_the_period:
                    if total_debit != 0 or total_credit != 0:
                        if not partner.ref_company_ids:
                            vals = {
			                    'name': partner.display_name,
			                    'partner_id': partner.id,
			                    'opening_balance': opening_balance,
			                    'debit': total_debit,
			                    'credit': total_credit,
			                    'closing_balance': cumulative_balance,
			                    'balance_currency': sum(line.amount_currency for line in lines),
			                }
                            line_list.append((0, 0, vals))
                else:
		               	# Summarize the results for each partner
                    if not partner.ref_company_ids:
                        vals = {
			                    'name': partner.display_name,
			                    'partner_id': partner.id,
			                    'opening_balance': opening_balance,
			                    'debit': total_debit,
			                    'credit': total_credit,
			                    'closing_balance': cumulative_balance,
			                    'balance_currency': sum(line.amount_currency for line in lines),
			            }
                        line_list.append((0, 0, vals))
            
            # Assign computed lines to the partner summary
            rec.partner_summary_line_ids = line_list
                
                
        
        
    # def apply_action(self):
    #
    #     # if self.difference > 0:
    #     #     raise UserError("Allocation Amount can not be higher than the Payment")
    #     move_line_list = []
    #     active_id = self.env.context.get('active_id')
    #     if active_id:
    #         move_line = self.env['account.move.line'].browse(active_id)
    #         move_line_list.append(move_line.id)
    #         line_list = []
    #         for line in self.match_line_ids:
    #             if line.allocation != 0:
    #                 vals = {'move_line_id': line.move_line_id.id,
    #                         'date': line.move_line_id.date,
    #                         'reference': line.reference,
    #                         'amount_currency': line.move_line_id.amount_currency,
    #                         'currency_id': line.move_line_id.currency_id.id,
    #                         'amount_residual_currency': line.move_line_id.amount_residual_currency,
    #                         'allocation_bool' : line.allocation_bool,
    #                         'allocation' : line.allocation
    #                         }
    #                 line_list.append((0, 0, vals))
    #                 move_line_list.append(line.move_line_id.id)
    #         reconcile_line_list = self.sudo().env['account.move.line'].search([('id','in',move_line_list)])
    #         reconcile_id = move_line.account_match_line_ids = line_list
    #         reconcile_line_list.reconcile()
    #
    #
    # def default_get(self, fields):
    #     res = super(AccountMatchWiz, self).default_get(fields)
    #     active_id = self.env.context.get('active_id')
    #
    #     if active_id:
    #         move_line = self.env['account.move.line'].browse(active_id)
    #         res['account_id'] = move_line.account_id.id
    #         res['partner_id'] = move_line.partner_id.id
    #         res['amount_currency'] = move_line.amount_currency
    #         res['exchange_rate'] = move_line.move_id.exchange_rate
    #         res['amount'] = move_line.debit - move_line.credit
    #         res['currency_id'] = move_line.currency_id.id
    #         move_lines = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
    #                                                         ('amount_residual', '!=', 0.0),
    #                                                        ('partner_id', '=', move_line.partner_id.id),
    #                                                        ('account_id', '=', move_line.account_id.id),
    #                                                        ('id','!=', move_line.id)])
    #
    #         line_ids = []
    #         if move_line.account_match_line_ids:
    #             for move in move_line.account_match_line_ids:
    #                 line_ids.append((0, 0, {'match_id': self.id,
    #                                     'date': move.date,
    #                                     'amount_currency': move.amount_currency,
    #                                     'currency_id': move.currency_id.id,
    #                                     'amount_residual_currency': move.amount_residual_currency,
    #                                     # 'balance_lc': move.amount_residual,
    #
    #
    #                                     'reference' : move.reference,
    #                                     'move_line_id' : move.move_line_id.id,
    #                                     'allocation_bool' : move.allocation_bool,
    #                                     'allocation' : move.allocation
    #                                     }))
    #         else:
    #             for move in move_lines:
    #                 line_ids.append((0, 0, {'match_id': self.id,
    #                                     'date': move.date,
    #                                     'date_maturity': move.date_maturity,
    #                                     'amount_currency': move.amount_currency,
    #                                     'currency_id': move.currency_id.id,
    #                                     'amount_residual_currency': move.amount_residual_currency,
    #                                     'balance_lc': move.amount_residual,
    #                                     'reference' : move.move_id.name,
    #                                     'move_line_id' : move.id
    #                                     }))
    #
    #         res['match_line_ids'] = line_ids
    #
    #     return res
    #
    # @api.depends('amount_currency', 'match_line_ids.allocation')
    # def _compute_difference(self):
    #     for rec in self:
    #         total_allocation = sum(rec.match_line_ids.mapped('allocation_bc'))
    #         rec.difference = rec.amount + total_allocation
    #         # if rec.amount + total_allocation > 0:
    #         #     raise UserError("Allocation Amount can not be higher than the Payment")
    
    def partner_summary_xlsx(self):
       for obj in self:
            data = self.read()[0]
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            report_name = obj.name
            # One sheet by partner
            worksheet = workbook.add_worksheet(report_name[:31])
            # bold = workbook.add_format({'bold': True})
            # sheet.write(0, 0, obj.name, bold)
            design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 25,
                                                                 'font_name': 'Times New Roman',
                                                                 'text_wrap': True,
                                                                 # 'bg_color': 'blue', 'color' : 'white',
                                                                 'text_wrap': True, 'shrink': True}),
                          'heading_format_1': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   # 'bg_color': 'FFFFCC',
                                                                   # 'color': 'black',
                                                                   'border': False,
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_3': workbook.add_format({'align': 'center',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   # 'bg_color': 'FFFFCC',
                                                                   'color': 'black',
                                                                   'border': True,
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_2': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 12,
                                                                   'font_name': 'Times New Roman',
                                                                   'color': 'black',
                                                                   'border': False,
                                                                   'text_wrap': True, 'shrink': True}),
                          'merged_format': workbook.add_format({'align': 'center',
                                                                'valign': 'vjustify',
                                                                'bold': True, 'size': 17,
                                                                'font_name': 'Times New Roman',
                                                                # 'bg_color': 'blue', 'color' : 'white',
                                                                'text_wrap': True, 'shrink': True}),
                          'sub_heading_format': workbook.add_format({'align': 'right',
                                                                     'valign': 'vjustify',
                                                                     'bold': True, 'size': 11,
                                                                     'font_name': 'Times New Roman',
                                                                     # 'bg_color': 'yellow', 'color' : 'black',
                                                                     'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_left': workbook.add_format({'align': 'left',
                                                                          'valign': 'vjustify',
                                                                          'bold': False, 'size': 9,
                                                                          'font_name': 'Times New Roman',
                                                                          # 'bg_color': 'yellow', 'color' : 'black',
                                                                          'text_wrap': True, 'shrink': True}),
                          'sub_heading_format_center': workbook.add_format({'align': 'center',
                                                                            'valign': 'vjustify',
                                                                            'bold': True, 'size': 9,
                                                                            'font_name': 'Times New Roman',
                                                                            # 'bg_color': 'yellow', 'color' : 'black',
                                                                            'text_wrap': True, 'shrink': True}),
                          'bold': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                       'size': 11,
                                                       'text_wrap': True}),
                          'bold_center': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                              'size': 11,
                                                              'text_wrap': True,
                                                              'align': 'center',
                                                              'border': True, }),
                          'bold_border': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
                                                              'size': 11, 'text_wrap': True,
                                                              'border': True, }),
                          'date_format_border': workbook.add_format({'num_format': 'dd/mm/yyyy',
                                                              'font_name': 'Times New Roman', 'size': 11,
                                                              'align': 'center', 'text_wrap': True,
                                                              'border': True, }),
                          'date_format': workbook.add_format({'num_format': 'dd/mm/yyyy',
                                                              'font_name': 'Times New Roman', 'size': 11,
                                                              'align': 'center', 'text_wrap': True,
                                                              }),
                          'datetime_format': workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm:ss',
                                                                  'font_name': 'Times New Roman', 'size': 11,
                                                                  'align': 'center', 'text_wrap': True}),
                          'normal_format': workbook.add_format({'font_name': 'Times New Roman',
                                                                'size': 11, 'text_wrap': True, 'italic': True, 'bold': True, }),
                          'normal_format_right': workbook.add_format({'font_name': 'Times New Roman',
                                                                      'align': 'right', 'size': 11,
                                                                      'text_wrap': True}),
                          'normal_format_left': workbook.add_format({'font_name': 'Times New Roman',
                                                                      'align': 'left', 'size': 11,
                                                                      'text_wrap': True}),
                          'normal_format_central': workbook.add_format({'font_name': 'Times New Roman',
                                                                        'size': 11, 'align': 'center',
                                                                        'text_wrap': True,
                                                                        }),
                          'normal_format_central_border': workbook.add_format({'font_name': 'Times New Roman',
                                                                        'size': 11, 'align': 'center',
                                                                        'text_wrap': True,
                                                                        'border': True, }),
                          'amount_format': workbook.add_format({'num_format': '#,##0.00',
                                                                'font_name': 'Times New Roman',
                                                                'align': 'right', 'size': 11,
                                                                'text_wrap': True,
                                                                'border': True, }),
                          'amount_format_2': workbook.add_format({'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'bold': True,
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True,
                                                                  'border': True, }),
                          'amount_format_1': workbook.add_format({'num_format': '#,##0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'normal_num_bold': workbook.add_format({'bold': True, 'num_format': '#,##0.00',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                          'float_format': workbook.add_format({'num_format': '###0.00',
                                                                    'font_name': 'Times New Roman',
                                                                    'align': 'center', 'size': 11,
                                                                    'text_wrap': True,
                                                                    'border': False, }),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                                                                  }
       
            worksheet.set_column('A:A', 30)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 25)
            worksheet.set_column('D:D', 30)
            worksheet.set_column('E:E', 30)
            worksheet.set_column('F:F', 30)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 20)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('J:J', 20)
            worksheet.set_column('K:K', 20)
            worksheet.set_column('L:L', 20)
            worksheet.set_column('M:M', 20)
            worksheet.set_column('N:N', 20)
            worksheet.set_column('O:O', 20)
            worksheet.set_column('P:P', 20)
            worksheet.set_column('Q:Q', 30)
            worksheet.set_column('R:R', 20)
            worksheet.set_column('S:S', 20)
            worksheet.set_column('T:T', 20)
            worksheet.set_column('U:U', 20)
            worksheet.set_column('V:V', 20)
            worksheet.set_column('W:W', 20)
            worksheet.set_column('X:X', 20)
            worksheet.set_column('Y:Y', 20)
            worksheet.set_column('Z:Z', 20)
            worksheet.set_column('AA:AA', 20)
            current_year = datetime.date.today().strftime("%Y")
            current_month = datetime.date.today().strftime("%B")
            company_name = self.env.company.name
            worksheet.merge_range('A1:B1', company_name, design_formats['heading_format_2'])
            worksheet.merge_range('A2:B2', 'Partner Ledger', design_formats['heading_format_2'])
            worksheet.write(4, 0, 'From Date : ', design_formats['heading_format_1'])
            worksheet.write(4, 1, obj.from_date if obj.from_date else '', design_formats['date_format'])
            worksheet.write(5, 0, 'To Date : ', design_formats['heading_format_1'])
            worksheet.write(5, 1, obj.to_date if obj.to_date else '', design_formats['date_format'])
            worksheet.write(6, 0, 'Type : ', design_formats['heading_format_1'])
            # account_name = ''
            # if obj.account_ids:
            #     for account in obj.account_ids:
            #         account_name += account.display_name + ','
            worksheet.write(6, 1, obj.account_type if obj.account_type else '', design_formats['normal_format_central'])
            
            worksheet.write(4, 2, 'Partner(s) : ', design_formats['heading_format_1'])
            partner_name = ''
            if obj.partner_ids:
                for partner in obj.partner_ids:
                    partner_name += partner.name + ','
            worksheet.write(4, 3, partner_name, design_formats['normal_format_central'])
            worksheet.write(5, 2, 'Analytic Account : ', design_formats['heading_format_1'])
            worksheet.write(5, 3, obj.analytic_account_id.name if obj.analytic_account_id else '', design_formats['heading_format_1'])
            worksheet.write(6, 2, 'Label : ', design_formats['heading_format_1'])
            worksheet.write(6, 3, obj.label if obj.label else '', design_formats['heading_format_1'])
            worksheet.write(9, 0, 'Partner', design_formats['heading_format_3'])
            # worksheet.write(9, 1, 'Date', design_formats['heading_format_3'])
            # worksheet.write(9, 2, 'Reference', design_formats['heading_format_3'])
            # worksheet.write(9, 3, 'Label', design_formats['heading_format_3'])
            # worksheet.write(9, 4, 'Account', design_formats['heading_format_3'])
            # worksheet.write(9, 5, 'Partner', design_formats['heading_format_3'])
            # worksheet.write(9, 6, 'Analytic Account', design_formats['heading_format_3'])
            worksheet.write(9, 1, 'Opening Balance', design_formats['heading_format_3'])
            # worksheet.write(9, 2, 'Currency', design_formats['heading_format_3'])
            worksheet.write(9, 2, 'Debit', design_formats['heading_format_3'])
            worksheet.write(9, 3, 'Credit', design_formats['heading_format_3'])
            worksheet.write(9, 4, 'Closing Balance', design_formats['heading_format_3'])
            row = 9
            col = 0
            for line in obj.partner_summary_line_ids:
                row += 1
                worksheet.write(row, col, line.name if line.name else '', design_formats['normal_format_left'])
                # worksheet.write(row, col + 1, line.date if line.date else '', design_formats['date_format'])
                # worksheet.write(row, col + 2, line.ref if line.ref else '', design_formats['normal_format_central'])
                # worksheet.write(row, col + 3, line.label if line.label else '', design_formats['normal_format_central'])
                # worksheet.write(row, col + 4,line.account_id.display_name if line.account_id else '', design_formats['normal_format_central'])
                # worksheet.write(row, col + 5,line.partner_id.name if line.partner_id else '',design_formats['normal_format_central'])
                # worksheet.write(row, col + 6,line.analytic_account_id.name if line.analytic_account_id else '',design_formats['normal_format_central'])
                worksheet.write(row, col + 1, line.opening_balance if line.opening_balance else '', design_formats['normal_format_right'])
                # worksheet.write(row, col + 8,line.currency_id.name if line.currency_id else '',design_formats['normal_format_central'])
                worksheet.write(row, col + 2, line.debit, design_formats['normal_format_right'])
                worksheet.write(row, col + 3, line.credit, design_formats['normal_format_right'])
                worksheet.write(row, col + 4, line.closing_balance, design_formats['normal_format_right'])
            workbook.close()
            output.seek(0)
            result = base64.b64encode(output.read())
            report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'Partner Summary.xlsx'})
        
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xlsx' % (
                    report_id.id, 'Partner Summary'),
                'target': 'new',
            }
            output.close()
        
    # def print_xlsx(self):
    #     return self.env.ref('zb_financial_reports.partner_summary_xlsx_report').report_action(self)
    #
    
    def partner_summary_pdf(self):
       return self.env.ref('zb_financial_reports.action_partner_summary').report_action(self)

class PartnerSummaryWizardLine(models.TransientModel):
    _name = 'partner.summary.wiz.line'
    _description = 'Partner summary Line Ledger Wizard'
    
    name = fields.Char('Name')
    partner_summary_id = fields.Many2one('partner.summary.wiz', string='Partner Summary Wizard')
    # date = fields.Date('Date')
    # ref = fields.Char('Reference')
    # label = fields.Char("Label")
    # account_id = fields.Many2one('account.account','Account')
    partner_id = fields.Many2one('res.partner','Partner')
    # analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    opening_balance = fields.Float(string='Opening Balance')
    currency_id = fields.Many2one('res.currency',string='Currency')
    # company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    closing_balance = fields.Float(string='Closing Balance')
    balance_currency = fields.Float(string='Balance Currency')
    
    
    
    
    
    
    # def open_partner_ledger(self):
    #     for rec in self:
    #         line_list = []
    #         opening_balance = sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('debit')) - sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('credit'))
    #         opening_balance_currency = sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('amount_currency'))
    #         line_list.append((0, 0, {'name':rec.partner_id.display_name,'ref':'Opening Balance','balance':opening_balance,'balance_currency':opening_balance_currency}))
    #
    #
    #         domain = [('parent_state','=','posted')]
    #         if rec.partner_summary_id.from_date:
    #             domain.append(('date','>=',rec.partner_summary_id.from_date))
    #         if rec.partner_summary_id.to_date:
    #             domain.append(('date','<=',rec.partner_summary_id.to_date))
    #         # if rec.analytic_account_id:
    #         #     domain.append(('analytic_account_id','=',rec.analytic_account_id.id))
    #         if rec.partner_summary_id.account_ids:
    #             domain.append(('account_id','in',rec.partner_summary_id.account_ids.ids))
    #
    #
    #         line_ids = self.env['account.move.line'].search(domain,order='date asc,id asc')
    #         account_ids = set(self.env['account.move.line'].search(domain).mapped('account_id'))
    #         # partner_ids = set(self.env['account.move.line'].browse(rec.partner_id.id))
    #
    #         # line_list = []
    #         # for partner in partner_ids:
    #         # opening_balance = sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('debit')) - sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('credit'))
    #         # opening_balance_currency = sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('amount_currency'))
    #         # line_list.append((0, 0, {'name':rec.partner_id.display_name,'ref':'Opening Balance','balance':opening_balance,'balance_currency':opening_balance_currency}))
    #
    #         # opening_balance = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted'),('account_type','in',['asset_receivable','liability_payable'])]).mapped('debit')) - sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted')]).mapped('credit'))
    #         # opening_balance_currency = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted'),('account_type','in',['asset_receivable','liability_payable'])]).mapped('amount_currency'))
    #         # line_list.append((0, 0, {'name':partner.display_name,'ref':'Opening Balance','balance':opening_balance,'balance_currency':opening_balance_currency}))
    #         for line in line_ids:
    #             if line.move_id.partner_id == rec.partner_id:
    #                 # vals = {
    #                 #     # 'move_line_id': line.move_line_id.id,
    #                 #             'date': line.date,
    #                 #             'ref': line.move_id.name,
    #                 #             'label': line.name,
    #                 #             'account_id': line.account_id.id,
    #                 #             'partner_id': line.partner_id.id,
    #                 #             'analytic_account_id': line.analytic_account_id.id,
    #                 #             'amount_currency': line.amount_currency,
    #                 #             'currency_id': line.currency_id.id,
    #                 #
    #                 #             'debit': line.debit,
    #                 #             'credit': line.credit,
    #                 #             'balance': opening_balance + (line.debit-line.credit),
    #                 #             'balance_currency' : opening_balance_currency + line.amount_currency
    #                 #
    #                 #             }
    #                 vals = {
    #         # 'move_line_id': line.move_line_id.id,
    #                 'date': line.date,
    #                 'ref': line.move_id.name,
    #                 'label': line.name,
    #                 'account_id': line.account_id.id,
    #                 'partner_id': rec.partner_id.id,
    #                 'analytic_account_id': line.analytic_account_id.id,
    #                 'amount_currency': line.amount_currency,
    #                 'currency_id': line.currency_id.id,
    #
    #                 'debit': line.debit,
    #                 'credit': line.credit,
    #                 'balance': opening_balance + (line.debit-line.credit),
    #                 'balance_currency' : opening_balance_currency + line.amount_currency,
    #                 'move_line_id':line.id
    #                 }
    #                 line_list.append((0, 0, vals))
    #                 opening_balance = opening_balance + (line.debit-line.credit)
    #                 opening_balance_currency = opening_balance_currency + line.amount_currency
    #
    #         # for line in line_ids:
    #         #     if line.partner_id == partner:
    #         # vals = {
    #         #     # 'move_line_id': line.move_line_id.id,
    #         #             # 'date': rec.date,
    #         #             # 'ref': rec.move_id.name,
    #         #             # 'label': rec.name,
    #         #             # 'account_id': rec.account_id.id,
    #         #             'partner_id': rec.partner_id.id,
    #         #             # 'analytic_account_id': line.analytic_account_id.id,
    #         #             # 'amount_currency': rec.amount_currency,
    #         #             'currency_id': rec.currency_id.id,
    #         #
    #         #             'debit': rec.debit,
    #         #             'credit': rec.credit,
    #         #             'balance': opening_balance + (rec.debit-rec.credit),
    #         #             'balance_currency' : rec.balance_currency
    #         #
    #         #             }
    #         # line_list.append((0, 0, vals))
    #         # opening_balance = opening_balance + (line.debit-line.credit)
    #         # opening_balance_currency = opening_balance_currency + line.amount_currency
    #
    #
    #
    #
    #
    #
    #
    #     return {
    #         'name': _('Partner Ledger'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'partner.ledger.wiz',
    #         'target': 'current',
    #         'context': {
    #                     'default_from_date' : rec.partner_summary_id.from_date,
    #                     'default_to_date' : rec.partner_summary_id.to_date,
    #                     'default_account_type' : rec.partner_summary_id.account_type,
    #                     'default_account_ids' : [(6,0,rec.partner_summary_id.account_ids.ids)],
    #                     'default_partner_ledger_line_ids' : line_list,
    #
    #                 }
    #         }
    def open_partner_ledger(self):
        for rec in self:
            line_list = []
            opening_balance = sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('debit')) - sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('credit'))
            opening_balance_currency = sum(self.env['account.move.line'].search([('partner_id','=',rec.partner_id.id),('date','<',rec.partner_summary_id.from_date),('parent_state','=','posted')]).mapped('amount_currency'))
            line_list.append((0, 0, {'name':rec.partner_id.display_name,'ref':'Opening Balance','balance':opening_balance,'balance_currency':opening_balance_currency}))
            
            domain = [('parent_state','=','posted')]
            if rec.partner_summary_id.from_date:
                domain.append(('date','>=',rec.partner_summary_id.from_date))
            if rec.partner_summary_id.to_date:
                domain.append(('date','<=',rec.partner_summary_id.to_date))
            if rec.partner_summary_id.account_ids:
                domain.append(('account_id','in',rec.partner_summary_id.account_ids.ids))
            
            line_ids = self.env['account.move.line'].search(domain, order='date asc, id asc')
            
            for line in line_ids:
                if line.move_id.partner_id == rec.partner_id:
                    vals = {
                        'date': line.date,
                        'ref': line.move_id.name,
                        'label': line.name,
                        'account_id': line.account_id.id,
                        'partner_id': rec.partner_id.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'amount_currency': line.amount_currency,
                        'currency_id': line.currency_id.id,
                        'debit': line.debit,
                        'credit': line.credit,
                        'balance': opening_balance + (line.debit - line.credit),
                        'balance_currency': opening_balance_currency + line.amount_currency,
                        'move_line_id': line.id
                    }
                    line_list.append((0, 0, vals))
                    opening_balance += (line.debit - line.credit)
                    opening_balance_currency += line.amount_currency
            print("========line_list,line_list===================================",line_list)
            ledger_wizard = self.env['partner.ledger.wiz'].create({
                'from_date': rec.partner_summary_id.from_date,
                'to_date': rec.partner_summary_id.to_date,
                'account_type': rec.partner_summary_id.account_type,
                'account_ids': [(6, 0, rec.partner_summary_id.account_ids.ids)],
                'partner_ids': [(6, 0, rec.partner_summary_id.partner_ids.ids)],
                'partner_ledger_line_ids': line_list,
            })
    
            return {
                'name': _('Partner Ledger'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'partner.ledger.wiz',
                'res_id': ledger_wizard.id,
                'target': 'current',
            }
    
    
