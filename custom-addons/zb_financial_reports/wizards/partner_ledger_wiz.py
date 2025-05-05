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
from datetime import datetime
from datetime import timedelta
import json
import io
from odoo.tools import date_utils
import base64

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
from datetime import date
from odoo import fields, models,api,_
from odoo.exceptions import ValidationError,UserError

class PartnerLedgerWizard(models.TransientModel):

    _name = 'partner.ledger.wiz'
    _description = 'Partner Ledger Wizard'
    
    # def _get_default_accounts(self):
    #     for rec in self:
    #         account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
    #         return account_ids.ids
    
    
    @api.model
    def default_get(self, fields_list):
        defaults = super(PartnerLedgerWizard, self).default_get(fields_list)

        if 'account_ids' in fields_list:
            defaults['account_ids'] = [
                (6, 0, self.env['account.account'].search([
                    ('account_type', 'in', ['asset_receivable', 'liability_payable'])
                ]).ids)
            ]
        return defaults
            
    name = fields.Char('Name',default = 'Partner Ledger')
    partner_ledger_line_ids = fields.One2many('partner.ledger.wiz.line', 'partner_ledger_id', string='Partner Ledger Wizard Lines')
    from_date = fields.Date('From Date',default=lambda self: date.today() - timedelta(days=30))
    to_date = fields.Date('To Date',default=fields.Date.context_today)
    account_type = fields.Selection([('asset_receivable','Receivable'),('liability_payable','Payable'),('receivable_payable','Receivable & Payable')],default='receivable_payable')
    account_ids = fields.Many2many('account.account','partner_ledger_account_rel','partner_ledg_id','accnt_id','Account(s)')
    partner_ids = fields.Many2many('res.partner','part_ledger_partner_rel','part_ledg_vend_id','part_vend_id','Partner(s)')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    label = fields.Char("Label")
    group_by = fields.Selection([('partner','Partner')],default='partner')
    company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    is_foreign_currency = fields.Boolean(string='Foreign Currency')
    show_draft = fields.Boolean(string='Show Draft Also')
    outstanding_only = fields.Boolean(string='Outstanding Only')
    child_partner_ids = fields.Many2many('res.partner','part_ledger_child_partner_rel','part_ledg_vendor_id','child_part_vend_id',string='Child Partner(s)')
    search_field=fields.Char("Search")
    company_id=fields.Many2one("res.company", default=lambda self: self.env.company.id)
    child_company_ids=fields.Many2many("res.company","company_partner_ledger_rel","company_id","partner_ledger_id",string="Child Company")
    
    
    @api.onchange('company_id')  
    def onchange_company_id(self):
        for rec in self:
            list1=[(5,0,0)] 
            for child in rec.company_id.child_ids:
                list1.append(child)                       
            rec.child_company_ids=[(6,0,rec.company_id.child_ids.ids)]  
            
    def _fetch_ledger_data(self):
        ledger_data = []
        for partner in self.partner_ids:
            opening_balance = self._compute_opening_balance(partner)
            cumulative_balance = opening_balance
            transactions = []
    
            salesperson_name = ''
            
            address = {
            'street': partner.street,
            'city': partner.city,
            'zip': partner.zip,
            'country': partner.country_id.name if partner.country_id else '',
        }
            first_move_line = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id),
                ('date', '>=', self.from_date),
                ('date', '<=', self.to_date),
                ('account_id', 'in', self.account_ids.ids)
            ], limit=1)
            if first_move_line and first_move_line.move_id.invoice_user_id:
                salesperson_name = first_move_line.move_id.invoice_user_id.name
    
            domain = [
                ('date', '>=', self.from_date),
                ('date', '<=', self.to_date),
                ('partner_id', '=', partner.id),
                ('account_id', 'in', self.account_ids.ids)
            ]
            if not self.show_draft:
                domain.append(('move_id.state', '=', 'posted'))
            
            move_lines = self.env['account.move.line'].search(domain, order='date')
    
            for line in move_lines:
                debit = line.debit
                credit = line.credit
                cumulative_balance += debit - credit
                transactions.append({
                    'date': line.date,
                    'doc_no': line.move_id.name,
                    'detail':  f"{line.move_id.name if line.move_id.name else ''}-" \
                               f"{line.move_id.ref if line.move_id.ref else ''} " \
                               f"[{line.date.strftime('%d/%m/%y') if line.date else ''}]",
                    'debit': debit,
                    'credit': credit,
                    'balance': cumulative_balance,
                     'journal_id': line.journal_id.id,
                })
    
            ledger_data.append({
                'partner': partner,
                'address': address,
                'salesperson': salesperson_name,
                'opening_balance': opening_balance,
                'transactions': transactions,
                'closing_balance': cumulative_balance,
            })
        print("============ledger_data=======================", ledger_data)
        return ledger_data
    
    def _compute_opening_balance(self, partner):
        opening_domain = [
            ('date', '<', self.from_date),
            ('partner_id', '=', partner.id),
            ('account_id', 'in', self.account_ids.ids)
        ]
        if not self.show_draft:
            opening_domain.append(('move_id.state', '=', 'posted'))
        
        move_lines = self.env['account.move.line'].search(opening_domain)
        opening_balance = sum(line.debit - line.credit for line in move_lines)
        return opening_balance

    def print_partner_ledger(self):
        return self.env.ref('zb_financial_reports.partner_ledger_reports').report_action(self, data={})
    
    @api.onchange('search_field')  
    def onchange_search(self):              
        for rec in self:
            print("=====rec.partner_ledger_line_ids======",rec.partner_ledger_line_ids)
            line_list=[]
            for line in rec.partner_ledger_line_ids:
                
                
                if(line.ref==rec.search_field or line.origin==rec.search_field
                    or line.vendor_bill==rec.search_field or line.label==rec.search_field
                    or line.analytic_account_id.name==rec.search_field):
                    pass
                else:
                    print("=====line========",line)
                    line_list.append(line)
            for line in line_list:
                line.unlink()

    
    @api.onchange('partner_ids')
    def onchange_partner_ids(self):
        for rec in self:
            child_partners = rec.partner_ids.mapped('child_ids')
            rec.child_partner_ids = [(6, 0, child_partners.ids)]
    
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
    #     analytic_fields = self.env['ir.model.fields'].sudo().search([('model_id.model', '=', 'account.analytic.line'), ('relation', '=', 'account.analytic.account')])
    #     for rec in self:
    #         rec.partner_ledger_line_ids = False
    #         if rec.show_draft == True:
    #             domain = [('parent_state','in',['posted','draft'])]
    #         else:
    #             domain = [('parent_state', '=', 'posted')]
    #
    #         if self.env.company:
    #             company_ids = self.env['res.company'].search([('parent_id','=',self.env.company.id)])
    #             if company_ids:
    #                 domain.append('|')
    #                 domain.append(('company_id','=',self.env.company.id))
    #                 domain.append(('company_id','in',company_ids.ids))
    #             else:
    #                 domain.append(('company_id','=',self.env.company.id))
    #         if rec.to_date:
    #             domain.append(('date','<=',rec.to_date))
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
    #         if rec.outstanding_only:
    #             domain.append(('amount_residual','not in',[0,-0,+0]))
    #
    #         line_ids = self.env['account.move.line'].search(domain,order='date asc,id asc')
    #         if rec.analytic_account_id:
    #             analytic_list=[]
    #             for line in line_ids:
    #                 #print("=======line==========",line)
    #                 for analytic_line in line.analytic_line_ids:
    #                     for analytic_field in analytic_fields:
    #                         if analytic_line[analytic_field.name]:
    #                             analytic_list.append(analytic_line[analytic_field.name])
    #
    #             domain.append(('analytic_account_id','in',analytic_list))
    #         partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
    #         if rec.from_date:
    #             domain.append(('date','>=',rec.from_date))
    #         line_ids = self.env['account.move.line'].search(domain,order='date asc,id asc')
    #         account_ids = set(self.env['account.move.line'].search(domain).mapped('account_id'))
    #
    #         if rec.group_by == 'partner':
    #             #print("======partner=====")
    #             line_list = []
    #             partners = []
    #             for partner in partner_ids:
    #                 partners.append(partner)
    #                 for child in rec.child_partner_ids:
    #                     partners.append(child)
    #
    #             for partner in partners:
    #                 opening_balance = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted'),('account_type','in',['asset_receivable','liability_payable'])]).mapped('debit')) - sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted')]).mapped('credit'))
    #                 opening_balance_currency = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted'),('account_type','in',['asset_receivable','liability_payable'])]).mapped('amount_currency'))
    #
    #                 opening_residual_currency = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<',rec.from_date),('parent_state','=','posted'),('account_type','in',['asset_receivable','liability_payable'])]).mapped('amount_residual'))
    #
    #                 if rec.outstanding_only:
    #                     line_list.append((0, 0, {'name':partner.display_name,'ref':'Opening Balance','original_balance':opening_balance,'residual_balance':opening_residual_currency}))
    #                 else:
    #                     line_list.append((0, 0, {'name':partner.display_name,'ref':'Opening Balance','balance':opening_balance,'balance_currency':opening_balance_currency}))
    #                 for line in line_ids:
    #                     analytic_list=[]
    #                     for analytic_line in line.analytic_line_ids:
    #                         for analytic_field in analytic_fields:
    #                             if analytic_line[analytic_field.name]:
    #                                 analytic_list.append(analytic_line[analytic_field.name])
    #
    #
    #
    #                     if line.partner_id == partner:
    #                         #print("hhhhhhhhhhhh")
    #                         if rec.outstanding_only:
    #                             vals = {
    #                                 # 'move_line_id': line.move_line_id.id,
    #                                         'date': line.date,
    #                                         'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                                         'label': line.name,
    #                                         'account_id': line.account_id.id,
    #                                         'partner_id': line.partner_id.id,
    #                                         'analytic_account_id': line.analytic_account_id.id,
    #                                         'amount_currency': line.amount_currency,
    #                                         'currency_id': line.currency_id.id,
    #                                         'move_line_id' : line.id,
    #                                         'original_balance': line.debit - line.credit,
    #                                         # 'credit': line.credit,
    #                                         'residual_balance': line.amount_residual,
    #                                         # 'balance_currency' : opening_balance_currency + line.amount_currency
    #
    #                                         }
    #                         else:
    #                             vals = {
    #                                 # 'move_line_id': line.move_line_id.id,
    #                                         'date': line.date,
    #                                         'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                                         'label': line.name,
    #                                         'account_id': line.account_id.id,
    #                                         'partner_id': line.partner_id.id,
    #                                         'analytic_account_id': line.analytic_account_id.id,
    #                                         'amount_currency': line.amount_currency,
    #                                         'currency_id': line.currency_id.id,
    #                                         'move_line_id' : line.id,
    #                                         'debit': line.debit,
    #                                         'credit': line.credit,
    #                                         'balance': opening_balance + (line.debit-line.credit),
    #                                         'balance_currency' : opening_balance_currency + line.amount_currency
    #
    #                                         }
    #
    #                         line_list.append((0, 0, vals))
    #                         opening_balance = opening_balance + (line.debit-line.credit)
    #                         opening_balance_currency = opening_balance_currency + line.amount_currency
    #
    #
    #
    #         else:
    #             line_list = []
    #             for line in line_ids:
    #
    #                 if rec.outstanding_only:
    #                     vals = {
    #                     # 'move_line_id': line.move_line_id.id,
    #                             'date': line.date,
    #                             'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                             'label': line.name,
    #                             'account_id': line.account_id.id,
    #                             'partner_id': line.partner_id.id,
    #                             'analytic_account_id': line.analytic_account_id.id,
    #                             'amount_currency': line.amount_currency,
    #                             'currency_id': line.currency_id.id,
    #                             'move_line_id' : line.id,
    #                             # 'debit': line.debit,
    #                             # 'credit': line.credit,
    #                             # 'balance': line.debit - line.credit,
    #                             # 'balance_currency' :  line.amount_currency
    #                             'original_balance': line.debit - line.credit,
    #                             'residual_balance': line.amount_residual,
    #
    #                             }
    #                 else:
    #                     vals = {
    #                         # 'move_line_id': line.move_line_id.id,
    #                                 'date': line.date,
    #                                 'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                                 'label': line.name,
    #                                 'account_id': line.account_id.id,
    #                                 'partner_id': line.partner_id.id,
    #                                 'analytic_account_id': line.analytic_account_id.id,
    #                                 'amount_currency': line.amount_currency,
    #                                 'currency_id': line.currency_id.id,
    #                                 'move_line_id' : line.id,
    #                                 'debit': line.debit,
    #                                 'credit': line.credit,
    #                                 'balance': line.debit - line.credit,
    #                                 'balance_currency' :  line.amount_currency
    #
    #                                 }
    #
    #                 line_list.append((0, 0, vals))
    #         #print("===============line_list",line_list)
    #         rec.partner_ledger_line_ids = line_list
    def load_data(self):
        analytic_fields = self.env['ir.model.fields'].sudo().search([
            ('model_id.model', '=', 'account.analytic.line'),
            ('relation', '=', 'account.analytic.account')
        ])
    
        for rec in self:
            rec.partner_ledger_line_ids = False
            # Set domain based on 'posted' or 'draft' status
            domain = [('parent_state', 'in', ['posted', 'draft'])] if rec.show_draft else [('parent_state', '=', 'posted')]
    
            # Filtering by company
            # if self.env.company:
            #     company_ids = self.env['res.company'].search([('parent_id', '=', self.env.company.id)])
            #     domain.append(('company_id', '=', self.env.company.id))
            #     if company_ids:
            #         domain.extend(['|', ('company_id', 'in', company_ids.ids)])
            
            
            company_ids = self.env.context.get('allowed_company_ids',[])
            if self.env.user.has_group('account.group_account_manager'):
                if company_ids:
                    # domain.append('|')
                    domain.append(('company_id','in',company_ids))
                else:
                    domain.append(('company_id','=',rec.company_id.id))
            else:
                domain.append(('company_id','=',rec.company_id.id))  
    
            # Apply additional filters
            if rec.from_date:
                domain.append(('date', '>=', rec.from_date))
            if rec.to_date:
                domain.append(('date', '<=', rec.to_date))
            if rec.analytic_account_id:
                domain.append(('analytic_account_id', '=', rec.analytic_account_id.id))
            if rec.account_ids:
                domain.append(('account_id', 'in', rec.account_ids.ids))
            if rec.account_type:
                account_type_map = {
                    'asset_receivable': ['asset_receivable'],
                    'liability_payable': ['liability_payable'],
                    'receivable_payable': ['asset_receivable', 'liability_payable']
                }
                domain.append(('account_type', 'in', account_type_map.get(rec.account_type, [])))
            if rec.partner_ids:
                domain.append(('partner_id', 'in', rec.partner_ids.ids))
            if rec.outstanding_only:
                domain.append(('amount_residual', '!=', 0))
    
            # Retrieve the filtered account move lines
            print("==== Domain ====", domain)
            line_ids = self.env['account.move.line'].search(domain, order='date asc, id asc')
            print("==== line_ids ====", line_ids)
    
            cumulative_balance = 0.0  # Initialize cumulative balance
    
            # Calculate opening balance for 'group by partner'
            line_list = []
            if rec.group_by == 'partner':
                partners = list(rec.partner_ids) + list(rec.child_partner_ids)
                for partner in partners:
                    # Calculate opening balance for each partner
                    opening_balance = sum(self.env['account.move.line'].search([
                        ('partner_id', '=', partner.id),
                        ('date', '<', rec.from_date),
                        ('parent_state', '=', 'posted'),
                        ('account_type', 'in', ['asset_receivable', 'liability_payable'])
                    ]).mapped(lambda x: x.debit - x.credit))
    
                    cumulative_balance = opening_balance  # Set initial cumulative balance
                    line_list.append((0, 0, {
                        'name': partner.display_name,
                        'ref': 'Opening Balance',
                        'balance': opening_balance,
                    }))
    
                    # Add transactions for the partner
                    for line in line_ids.filtered(lambda l: l.partner_id == partner):
                        cumulative_balance += line.debit - line.credit
                        vals = {
                            'date': line.date,
                            'ref': f"{line.move_id.name or ''}-{line.move_id.ref or ''} " \
                                   f"[{line.date.strftime('%d/%m/%y') if line.date else ''}]",
                            'label': line.name,
                            'account_id': line.account_id.id,
                            'partner_id': line.partner_id.id,
                            'analytic_account_id': line.analytic_account_id.id,
                            'amount_currency': line.amount_currency,
                            'currency_id': line.currency_id.id,
                            'move_line_id': line.id,
                            'debit': line.debit,
                            'credit': line.credit,
                            'balance': cumulative_balance,  # Cumulative balance here
                            'balance_currency': cumulative_balance + line.amount_currency,
                             'journal_id': line.journal_id.id,
                        }
                        line_list.append((0, 0, vals))
            else:
                # For non-partner group-by
                cumulative_balance = 0.0  # Initialize cumulative balance for non-grouped
                for line in line_ids:
                    cumulative_balance += line.debit - line.credit
                    vals = {
                        'date': line.date,
                        'ref': f"{line.move_id.name or ''}-{line.move_id.ref or ''} " \
                               f"[{line.date.strftime('%d/%m/%y') if line.date else ''}]",
                        'label': line.name,
                        'account_id': line.account_id.id,
                        'partner_id': line.partner_id.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'amount_currency': line.amount_currency,
                        'currency_id': line.currency_id.id,
                        'move_line_id': line.id,
                        'debit': line.debit,
                        'credit': line.credit,
                        'balance': cumulative_balance,  # Cumulative balance here
                        'balance_currency': cumulative_balance + line.amount_currency,
                         'journal_id': line.journal_id.id,
                    }
                    line_list.append((0, 0, vals))
    
            # Assign the cumulative balance lines to the partner ledger
            rec.partner_ledger_line_ids = line_list
    # def load_data(self):
    #     analytic_fields = self.env['ir.model.fields'].search([('model_id.model', '=', 'account.analytic.line'), ('relation', '=', 'account.analytic.account')])
    #     print("Analytic fields:", analytic_fields)
    #
    #     for rec in self:
    #         rec.partner_ledger_line_ids = False
    #         domain = [('parent_state', '=', 'posted')] if not rec.show_draft else [('parent_state', 'in', ['posted', 'draft'])]
    #
    #         if self.env.company:
    #             company_ids = self.env['res.company'].search([('parent_id', '=', self.env.company.id)])
    #             if company_ids:
    #                 domain.extend(['|', ('company_id', '=', self.env.company.id), ('company_id', 'in', company_ids.ids)])
    #             else:
    #                 domain.append(('company_id', '=', self.env.company.id))
    #         print("Domain after company filtering:", domain)
    #
    #         if rec.to_date:
    #             domain.append(('date', '<=', rec.to_date))
    #         if rec.analytic_account_id:
    #             domain.append(('analytic_account_id', '=', rec.analytic_account_id.id))
    #         if rec.account_ids:
    #             domain.append(('account_id', 'in', rec.account_ids.ids))
    #         if rec.account_type:
    #             if rec.account_type == 'asset_receivable':
    #                 domain.append(('account_type', '=', 'asset_receivable'))
    #             elif rec.account_type == 'liability_payable':
    #                 domain.append(('account_type', '=', 'liability_payable'))
    #             elif rec.account_type == 'receivable_payable':
    #                 domain.append(('account_type', 'in', ['asset_receivable', 'liability_payable']))
    #         else:
    #             domain.append(('account_type', 'in', ['asset_receivable', 'liability_payable']))
    #         if rec.partner_ids:
    #             domain.append(('partner_id', 'in', rec.partner_ids.ids))
    #         if rec.outstanding_only:
    #             domain.append(('amount_residual', 'not in', [0, -0, +0]))
    #
    #         print("Final domain before line_ids search:", domain)
    #         line_ids = self.env['account.move.line'].search(domain, order='date asc, id asc')
    #         print("Initial line_ids found:", line_ids)
    #
    #         if rec.analytic_account_id:
    #             analytic_list = []
    #             for line in line_ids:
    #                 for analytic_line in line.analytic_line_ids:
    #                     for analytic_field in analytic_fields:
    #                         if analytic_line[analytic_field.name]:
    #                             analytic_list.append(analytic_line[analytic_field.name])
    #             domain.append(('analytic_account_id', 'in', analytic_list))
    #             print("Analytic list after processing:", analytic_list)
    #
    #         partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
    #         print("Partner IDs mapped from domain:", partner_ids)
    #
    #         if rec.from_date:
    #             domain.append(('date', '>=', rec.from_date))
    #
    #         line_ids = self.env['account.move.line'].search(domain, order='date asc, id asc')
    #         print("line_ids after applying from_date:", line_ids)
    #
    #         account_ids = set(self.env['account.move.line'].search(domain).mapped('account_id'))
    #         print("Account IDs mapped from domain:", account_ids)
    #
    #         line_list = []
    #         if rec.group_by == 'partner':
    #             print("Grouping by partner")
    #             partners = list(partner_ids)
    #
    #             for partner in partners:
    #                 opening_balance = sum(self.env['account.move.line'].search([('partner_id', '=', partner.id), ('date', '<', rec.from_date), ('parent_state', '=', 'posted'), ('account_type', 'in', ['asset_receivable', 'liability_payable'])]).mapped('debit')) \
    #                                 - sum(self.env['account.move.line'].search([('partner_id', '=', partner.id), ('date', '<', rec.from_date), ('parent_state', '=', 'posted'),('account_type', 'in', ['asset_receivable', 'liability_payable'])]).mapped('credit'))
    #                 print("========debit======upto from=======")
    #                 print("========credit============")
    #                 opening_balance_currency = sum(self.env['account.move.line'].search([('partner_id', '=', partner.id), ('date', '<', rec.from_date), ('parent_state', '=', 'posted'), ('account_type', 'in', ['asset_receivable', 'liability_payable'])]).mapped('amount_currency'))
    #                 opening_residual_currency = sum(self.env['account.move.line'].search([('partner_id', '=', partner.id), ('date', '<', rec.from_date), ('parent_state', '=', 'posted'), ('account_type', 'in', ['asset_receivable', 'liability_payable'])]).mapped('amount_residual'))
    #
    #                 print(f"=======Opening balances for partner {partner.display_name}: Balance={opening_balance}, Currency Balance={opening_balance_currency}, Residual Balance={opening_residual_currency}")
    #
    #                 if rec.outstanding_only:
    #                     line_list.append((0, 0, {'name': partner.display_name, 'ref': 'Opening Balance', 'original_balance': opening_balance, 'residual_balance': opening_residual_currency}))
    #                 else:
    #                     line_list.append((0, 0, {'name': partner.display_name, 'ref': 'Opening Balance', 'balance': opening_balance, 'balance_currency': opening_balance_currency}))
    #
    #                 for line in line_ids:
    #                     analytic_list = []
    #                     for analytic_line in line.analytic_line_ids:
    #                         for analytic_field in analytic_fields:
    #                             if analytic_line[analytic_field.name]:
    #                                 analytic_list.append(analytic_line[analytic_field.name])
    #
    #                     if line.partner_id == partner:
    #                         if rec.outstanding_only:
    #                             vals = {
    #                                 'date': line.date,
    #                                 'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                                 'label': line.name,
    #                                 'account_id': line.account_id.id,
    #                                 'partner_id': line.partner_id.id,
    #                                 'analytic_account_id': line.analytic_account_id.id,
    #                                 'amount_currency': line.amount_currency,
    #                                 'currency_id': line.currency_id.id,
    #                                 'move_line_id': line.id,
    #                                 'original_balance': line.debit - line.credit,
    #                                 'residual_balance': line.amount_residual,
    #                             }
    #                         else:
    #                             vals = {
    #                                 'date': line.date,
    #                                 'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                                 'label': line.name,
    #                                 'account_id': line.account_id.id,
    #                                 'partner_id': line.partner_id.id,
    #                                 'analytic_account_id': line.analytic_account_id.id,
    #                                 'amount_currency': line.amount_currency,
    #                                 'currency_id': line.currency_id.id,
    #                                 'move_line_id': line.id,
    #                                 'debit': line.debit,
    #                                 'credit': line.credit,
    #                                 'balance': opening_balance + (line.debit - line.credit),
    #                                 'balance_currency': opening_balance_currency + line.amount_currency,
    #                             }
    #                             print("=================================Working Part================================")
    #                         print("Appending line values:", vals)
    #                         line_list.append((0, 0, vals))
    #                         opening_balance += (line.debit - line.credit)
    #                         opening_balance_currency += line.amount_currency
    #         else:
    #             for line in line_ids:
    #                 if rec.outstanding_only:
    #                     vals = {
    #                         'date': line.date,
    #                         'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                         'label': line.name,
    #                         'account_id': line.account_id.id,
    #                         'partner_id': line.partner_id.id,
    #                         'analytic_account_id': line.analytic_account_id.id,
    #                         'amount_currency': line.amount_currency,
    #                         'currency_id': line.currency_id.id,
    #                         'move_line_id': line.id,
    #                         'original_balance': line.debit - line.credit,
    #                         'residual_balance': line.amount_residual,
    #                     }
    #                 else:
    #                     vals = {
    #                         'date': line.date,
    #                         'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                         'label': line.name,
    #                         'account_id': line.account_id.id,
    #                         'partner_id': line.partner_id.id,
    #                         'analytic_account_id': line.analytic_account_id.id,
    #                         'amount_currency': line.amount_currency,
    #                         'currency_id': line.currency_id.id,
    #                         'move_line_id': line.id,
    #                         'debit': line.debit,
    #                         'credit': line.credit,
    #                         'balance': line.debit - line.credit,
    #                         'balance_currency': line.amount_currency,
    #                     }
    #                 print("Appending line values in else block:", vals)
    #                 line_list.append((0, 0, vals))
    #
    #         print("Final line list to assign:", line_list)
    #         rec.partner_ledger_line_ids = line_list
    def print_partner_ledger_xlsx(self):
        for obj in self:
            data = self.read()[0]
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            report_name = obj.name
            # One sheet by partner
            worksheet = workbook.add_worksheet(report_name[:31])
            total_debit = 0.0
            total_credit =0.0
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
                          'heading_format_2': workbook.add_format({'align': 'center',
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
            worksheet.set_column('AA:AA',20)
            current_year = date.today().strftime("%Y")
            current_month = date.today().strftime("%B")
            company_name = self.env.company.name
            worksheet.merge_range('F1:H1', company_name, design_formats['heading_format_2'])
            worksheet.merge_range('F2:H2', 'Partner Ledger', design_formats['heading_format_2'])
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
            worksheet.write(9, 0, 'Name', design_formats['heading_format_3'])
            worksheet.write(9, 1, 'Date', design_formats['heading_format_3'])
            worksheet.write(9, 2, 'Reference', design_formats['heading_format_3'])
            worksheet.write(9, 3, 'Label', design_formats['heading_format_3'])
            worksheet.write(9, 4, 'Account', design_formats['heading_format_3'])
            worksheet.write(9, 5, 'Partner', design_formats['heading_format_3'])
            worksheet.write(9, 6, 'Analytic Account', design_formats['heading_format_3'])
            if obj.is_foreign_currency:
                worksheet.write(9, 7, 'Amount Currency', design_formats['heading_format_3'])
                worksheet.write(9, 8, 'Currency', design_formats['heading_format_3'])
                worksheet.write(9, 9, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 10, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 11, 'Balance', design_formats['heading_format_3'])
                worksheet.write(9, 12, 'Balance Currency', design_formats['heading_format_3'])
            else:
                worksheet.write(9, 7, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 8, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 9, 'Balance', design_formats['heading_format_3'])
            row = 9
            col = 0
            for line in obj.partner_ledger_line_ids:
                print("1111111111111111111111111111111")
                row += 1
                worksheet.write(row, col, line.name if line.name else '', design_formats['normal_format_left'])
                worksheet.write(row, col + 1, line.date if line.date else '', design_formats['date_format'])
                worksheet.write(row, col + 2, line.ref if line.ref else '', design_formats['normal_format_central'])
                worksheet.write(row, col + 3, line.label if line.label else '', design_formats['normal_format_central'])
                worksheet.write(row, col + 4,line.account_id.display_name if line.account_id else '', design_formats['normal_format_central'])
                worksheet.write(row, col + 5,line.partner_id.name if line.partner_id else '',design_formats['normal_format_central'])
                worksheet.write(row, col + 6,line.analytic_account_id.name if line.analytic_account_id else '',design_formats['normal_format_central'])
                if obj.is_foreign_currency:
                    worksheet.write(row, col + 7,line.amount_currency if line.amount_currency else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 8,line.currency_id.name if line.currency_id else '',design_formats['normal_format_central'])
                    worksheet.write(row, col + 9,line.debit,design_formats['normal_format_right'])
                    worksheet.write(row, col + 10,line.credit,design_formats['normal_format_right'])
                    worksheet.write(row, col + 11,line.balance,design_formats['normal_format_right'])
                    worksheet.write(row, col + 12,line.balance_currency,design_formats['normal_format_right'])
                    total_debit += line.debit
                    total_credit += line.credit
                else:
                    worksheet.write(row, col + 7,line.debit,design_formats['normal_format_right'])
                    worksheet.write(row, col + 8,line.credit,design_formats['normal_format_right'])
                    worksheet.write(row, col + 9,line.balance,design_formats['normal_format_right'])
                    total_debit += line.debit
                    total_credit += line.credit
            print("row,debit,credit----------------------",row,total_debit,total_credit)
            row += 2  # Add an empty row for separation
            if obj.is_foreign_currency:
                worksheet.write(row, col + 9, total_debit, design_formats['amount_format_2'])
                worksheet.write(row, col + 10, total_credit, design_formats['amount_format_2'])
            else:
                worksheet.write(row, col + 7, total_debit, design_formats['amount_format_2'])
                worksheet.write(row, col + 8, total_credit, design_formats['amount_format_2'])
            workbook.close()
            output.seek(0)
            result = base64.b64encode(output.read())
            report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'Partner Ledger.xlsx'})
        
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xlsx' % (
                    report_id.id, 'Partner Ledger'),
                'target': 'new',
            }
            output.close()
    
    # def print_xlsx(self):
    #     return self.env.ref('zb_financial_reports.partner_ledger_xlsx_report').report_action(self)
    
class PartnerLedgerWizardLine(models.TransientModel):
    _name = 'partner.ledger.wiz.line'
    _description = 'Partner Ledger Line Wizard'
    
    name = fields.Char('Name')
    origin = fields.Char('Origin')
    partner_ledger_id = fields.Many2one('partner.ledger.wiz', string='Partner Ledger Wizard')
    date = fields.Date('Date')
    ref = fields.Char('Reference')
    label = fields.Char("Label")
    account_id = fields.Many2one('account.account','Account')
    partner_id = fields.Many2one('res.partner','Partner')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    amount_currency = fields.Float(string='Amount Currency')
    currency_id = fields.Many2one('res.currency',string='Currency')
    # company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    balance = fields.Float(string='Balance')
    balance_currency = fields.Float(string='Balance Currency')
    move_line_id = fields.Many2one('account.move.line',string="Move Line")
    journal_id = fields.Many2one('account.journal', string='Journal') 

    
    # original_opening = fields.Float(string='Opening Balance')
    original_balance = fields.Float(string='Original')
    # residual_opening = fields.Float(string='Opening Balance')
    residual_balance = fields.Float(string='Residual')
    
    
    
    def open_account_move(self):
        for rec in self:
            return {
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'account.move',
                        'target': 'current',
                        'res_id': rec.move_line_id.move_id.id,
                        'context': self.env.context,
                    }
    
    
    
    
    
