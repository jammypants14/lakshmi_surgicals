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
import json
from odoo.tools import date_utils
import io
from odoo import fields, models, api,_
from odoo.exceptions import ValidationError, UserError
import base64
import datetime
from datetime import date, timedelta

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class TrialBalanceWizard(models.TransientModel):

    _name = 'trial.balance.wiz'
    _description = 'Trial Balance Wizard'
    
    name = fields.Char('Name', default='Trial Balance')
    trial_balance_line_ids = fields.One2many('trial.balance.wiz.line', 'trial_balance_id', string='Trial Balance Wizard Lines')
    trial_balance_complete_line_ids = fields.One2many('trial.balance.wiz.complete.line', 'trial_balance_id', string='Trial Balance Wizard Complete Lines')
    from_date = fields.Date('From Date',default=lambda self: date(date.today().year, 1, 1))
    to_date = fields.Date('To Date',default=fields.Date.context_today)
    display_type = fields.Selection([('balance_only', 'Balance Only'), ('complete', 'Complete')],default='balance_only')
    account_ids = fields.Many2many('account.account',string='Account(s)')
    
    
    # account_ids = fields.Many2many('account.account', 'trial_bal_account_rel', 'trial_bal_id', 'accn_id', 'Account(s)')
    # partner_ids = fields.Many2many('res.partner', 'trial_bal_partner_rel', 'trial_bal_vend_id', 'ven_id', 'Partner(s)')
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    # label = fields.Char("Label")
    # group_by = fields.Selection([('account', 'Account'), ('partner', 'Partner')])
    
    # currency_id = fields.Many2one('res.currency',string='Currency')
    # company_currency_id = fields.Many2one('res.currency', string='Company Currency', default=lambda self: self.env.user.company_id.currency_id.id)
    hide_zero_balance = fields.Boolean("Hide Zero Balance",default=True)
    # amount = fields.Monetary(string='Amount', currency_field='company_currency_id')
    show_draft = fields.Boolean(string='Show Draft Also')
    company_id=fields.Many2one("res.company", default=lambda self: self.env.company.id)
    child_company_ids=fields.Many2many("res.company","company_trial_rel","company_id","trial_balance_id",string="Child Company")
    
    @api.model
    def default_get(self, fields):
        res = super(TrialBalanceWizard, self).default_get(fields)
        if self.env.context.get('balance_sheet') == True:
            res['sheet_type'] = 'balance_sheet'
            res['name'] = 'Balance Sheet'
        elif self.env.context.get('profit_loss') == True:
            res['sheet_type'] = 'profit_loss'
            res['name'] = 'Profit & Loss'
        else:
            res['sheet_type'] = 'trial_balance'
            res['name'] = 'Trial Balance'
        return res
    
    show_debit_credit = fields.Boolean(string='Show Debit & Credit', default=False)
    sheet_type = fields.Selection(
        selection=[
            ("balance_sheet", "Balance Sheet"),
            ("profit_loss", "Profit & Loss"),
            ("trial_balance", "Trial Balance"),
        ],
        string="Type"
    )
    
    @api.onchange('company_id')  
    def onchange_company_id(self):
        for rec in self:
            list1=[(5,0,0)] 
            for child in rec.company_id.child_ids:
                list1.append(child)                       
            rec.child_company_ids=[(6,0,rec.company_id.child_ids.ids)]  
            
    def load_data(self):
        domain = []
        cr = self.env.cr
        for rec in self:
            # Reset the result fields
            rec.trial_balance_line_ids = False
            rec.trial_balance_complete_line_ids = False
    
            # Determine state(s) condition based on rec.show_draft
            if rec.show_draft:
                state_list = ('posted', 'draft')
            else:
                state_list = ('posted',)
    
            # Build company filter
            company_clause = ""
            params_company = []
            # company_ids = self.env.context.get('allowed_company_ids',[])
            # if self.env.user.has_group('account.group_account_manager'):
            #     if company_ids:
            #         # domain.append('|')
            #         domain.append(('company_id','in',company_ids))
            # if self.env.company:
            #     company_ids = self.env['res.company'].search([('parent_id', '=', self.env.company.id)])
            #     if company_ids:
            #         # Using SQL IN clause; note that we pass a tuple of ids.
            #         company_clause = "AND (company_id = %s OR company_id IN %s)"
            #         params_company = [self.env.company.id, tuple(company_ids.ids)]
            #     else:
            #         company_clause = "AND company_id = %s"
            #         params_company = [self.env.company.id]
            
            if self.env.user.has_group('account.group_account_manager'):
                allowed_company_ids = self.env.context.get('allowed_company_ids', [])
                if allowed_company_ids:
                    # Use the allowed companies from the context
                    domain.append(('company_id', 'in', allowed_company_ids))
                    company_clause = "AND company_id IN %s"
                    params_company = [tuple(allowed_company_ids)]
                else:
                    company_clause = "AND company_id = %s"
                    params_company = [self.env.company.id]
            else:
                company_clause = "AND company_id = %s"
                params_company = [self.env.company.id]
                
            # if self.env.user.has_group('account.group_account_manager'):
            #     allowed_company_ids = self.env.context.get('allowed_company_ids', [])
            #     if allowed_company_ids:
            #         # If you plan to use the domain later, initialize it first.
            #         domain = []  # Initialize domain if not already defined
            #         domain.append(('company_id', 'in', allowed_company_ids))
            #         company_clause = "AND company_id IN %s"
            #         params_company = [tuple(allowed_company_ids)]
            #     else:
            #         company_clause = "AND company_id = %s"
            #         params_company = [self.env.company.id]
            # else:
            #     company_ids = self.env['res.company'].search([('parent_id', '=', self.env.company.id)])
            #     if company_ids:
            #         # Using SQL IN clause; note that we pass a tuple of ids.
            #         company_clause = "AND (company_id = %s OR company_id IN %s)"
            #         params_company = [self.env.company.id, tuple(company_ids.ids)]
            #     else:
            #         company_clause = "AND company_id = %s"
            #         params_company = [self.env.company.id]        

    
            # Build date conditions for the period (from_date to to_date)
            period_conditions = ""
            period_params = []
            if rec.from_date:
                period_conditions += " AND date >= %s"
                period_params.append(rec.from_date)
            if rec.to_date:
                period_conditions += " AND date <= %s"
                period_params.append(rec.to_date)
    
            # Build date condition for records before the period (for opening balance)
            before_conditions = ""
            before_params = []
            if rec.from_date:
                before_conditions += " AND date < %s"
                before_params.append(rec.from_date)
    
            # ---------------------------
            # Query 1: Aggregate data for the period
            # ---------------------------
            query_period = f"""
                SELECT account_id,
                       COALESCE(SUM(debit), 0) AS debit_period,
                       COALESCE(SUM(credit), 0) AS credit_period
                FROM account_move_line
                WHERE parent_state IN %s
                  {company_clause}
                  {period_conditions}
                GROUP BY account_id
            """
            period_query_params = [state_list] + params_company + period_params
            cr.execute(query_period, period_query_params)
            period_data = cr.dictfetchall()
            # Map results by account_id for quick lookup
            period_dict = {row['account_id']: row for row in period_data if row['account_id']}
    
            # ---------------------------
            # Query 2: Aggregate data for records BEFORE the period (for opening balances)
            # ---------------------------
            query_before = f"""
                SELECT account_id,
                       COALESCE(SUM(debit), 0) AS debit_before,
                       COALESCE(SUM(credit), 0) AS credit_before,
                       COALESCE(SUM(amount_currency), 0) AS amount_currency_before
                FROM account_move_line
                WHERE parent_state IN %s
                  {company_clause}
                  {before_conditions}
                GROUP BY account_id
            """
            before_query_params = [state_list] + params_company + before_params
            cr.execute(query_before, before_query_params)
            before_data = cr.dictfetchall()
            before_dict = {row['account_id']: row for row in before_data if row['account_id']}
    
            # Determine which account IDs to consider (those that appear in either query)
            all_account_ids = set(period_dict.keys()) | set(before_dict.keys())
    
            # Filter accounts based on the context
            if self.env.context.get('profit_loss'):
                domain = [('id', 'in', list(all_account_ids)), ('include_initial_balance', '=', False)]
            elif self.env.context.get('balance_sheet'):
                domain = [('id', 'in', list(all_account_ids)), ('include_initial_balance', '=', True)]
            else:
                domain = [('id', 'in', list(all_account_ids))]
    
            accounts = self.env['account.account'].search(domain, order='code asc')
    
            line_list = []
            line_complete_list = []
            total_opening = total_debit = total_credit = 0.0
    
            for account in accounts:
                # Get aggregated values from the SQL queries; default to 0.0 if not present
                bvals = before_dict.get(account.id, {})
                pvals = period_dict.get(account.id, {})
    
                debit_before = bvals.get('debit_before', 0.0)
                credit_before = bvals.get('credit_before', 0.0)
                opening_balance = debit_before - credit_before
    
                debit_period = pvals.get('debit_period', 0.0)
                credit_period = pvals.get('credit_period', 0.0)
                opening_balance2 = debit_period - credit_period
                opening_balance3 = opening_balance + opening_balance2
                debit3 = debit_before + debit_period
                credit3 = credit_before + credit_period
                closing_balance = opening_balance + (debit_period - credit_period)
                if self.env.context.get('profit_loss'): 
                    closing_balance = opening_balance + (credit_period-debit_period)
    
                # Check hide_zero_balance flag
                val_flag = True
                if rec.hide_zero_balance:
                    if (opening_balance == 0 and closing_balance == 0 and
                        debit_period == 0 and credit_period == 0):
                        val_flag = False
    
                if val_flag:
                    vals = {
                        'name': account.name,
                        'code': account.code,
                        'type': account.account_type,
                        'account_id': account.id,
                        'debit': debit_period,
                        'credit': credit_period,
                        'opening_balance': opening_balance,
                        'closing_balance': closing_balance,
                    }
                    line_list.append((0, 0, vals))
    
                # Build the complete line
                vals2 = {
                    'name': account.name,
                    'code': account.code,
                    'type': account.account_type,
                    'account_id': account.id,
                    'debit1': debit_before,
                    'credit1': credit_before,
                    'opening_balance1': opening_balance,
                    'debit2': debit_period,
                    'credit2': credit_period,
                    'opening_balance2': opening_balance2,
                    'debit3': debit3,
                    'credit3': credit3,
                    'opening_balance3': opening_balance3,
                }
                line_complete_list.append((0, 0, vals2))
    
                if self.env.context.get('balance_sheet'):
                    total_opening += opening_balance
                    total_debit += debit_period
                    total_credit += credit_period
    
            # For balance sheet, add unallocated earnings if totals exist
            if self.env.context.get('balance_sheet'):
                if total_opening != 0.0:
                    vals = {
                        'name': f'Unallocated Earnings Till {rec.to_date:%d/%m/%Y}',
                        'opening_balance': -total_opening,
                        'closing_balance': -total_opening,
                    }
                    line_list.append((0, 0, vals))
                if total_debit or total_credit:
                    if total_debit > total_credit:
                        balanc = total_debit - total_credit
                        if balanc:
                            vals = {
                                'name': 'Unallocated Earnings - Current Period',
                                'credit': balanc,
                                'closing_balance': -balanc,
                            }
                            line_list.append((0, 0, vals))
                    else:
                        balanc = total_credit - total_debit
                        if balanc:
                            vals = {
                                'name': 'Unallocated Earnings - Current Period',
                                'debit': balanc,
                                'closing_balance': -balanc,
                            }
                            line_list.append((0, 0, vals))
    
            rec.trial_balance_line_ids = line_list
            rec.trial_balance_complete_line_ids = line_complete_list

    
    
    def print_trial_balance_xlsx(self):
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
                          'heading_format_2': workbook.add_format({'align': 'center',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 12,
                                                                   'font_name': 'Times New Roman',
                                                                   'color': 'black',
                                                                   'border': False,
                                                                   'text_wrap': True, 'shrink': True}),
                          'heading_format_4': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   # 'bg_color': 'FFFFCC',
                                                                   'color': 'black',
                                                                   'border': True,
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
        
        current_year = datetime.date.today().strftime("%Y")
        current_month = datetime.date.today().strftime("%B")
        company_name = self.env.company.name
        worksheet.merge_range('D1:F1', company_name, design_formats['heading_format_2'])
        
        # worksheet.merge_range('D2:F2', 'Trial Balance', design_formats['heading_format_2'])
        if obj.sheet_type == 'trial_balance':
            worksheet.merge_range('D1:F1', company_name, design_formats['heading_format_2'])
            worksheet.merge_range('D2:F2', 'Trial Balance', design_formats['heading_format_2'])
        elif obj.sheet_type == 'balance_sheet':
            worksheet.merge_range('D1:F1', company_name, design_formats['heading_format_2'])
            worksheet.merge_range('D2:F2', 'Balance Sheet', design_formats['heading_format_2'])
        elif obj.sheet_type == 'profit_loss':
            worksheet.merge_range('C1:D1', company_name, design_formats['heading_format_2'])
            worksheet.merge_range('C2:D2', 'Profit & Loss', design_formats['heading_format_2'])
        worksheet.write(4, 0, 'From Date : ', design_formats['heading_format_1'])
        worksheet.write(4, 1, obj.from_date if obj.from_date else '', design_formats['date_format'])
        worksheet.write(5, 0, 'To Date : ', design_formats['heading_format_1'])
        worksheet.write(5, 1, obj.to_date if obj.to_date else '', design_formats['date_format'])
        
        worksheet.write(6, 0, 'Display Type : ', design_formats['heading_format_1'])
        display_type = ''
        if obj.display_type == 'balance_only':
            display_type = 'Balance Only'
        elif obj.display_type == 'complete':
            display_type = 'Complete'
            
            
        worksheet.write(6, 1, display_type, design_formats['normal_format_central'])
        #
        # worksheet.write(4, 2, 'Partner(s) : ', design_formats['heading_format_1'])
        # partner_name = ''
        # if obj.partner_ids:
        #     for partner in obj.partner_ids:
        #         partner_name += partner.name + ','
        # worksheet.write(4, 3, partner_name, design_formats['normal_format_central'])
        # worksheet.write(5, 2, 'Analytic Account : ', design_formats['heading_format_1'])
        # worksheet.write(5, 3, obj.analytic_account_id.name if obj.analytic_account_id else '', design_formats['heading_format_1'])
        # worksheet.write(6, 2, 'Label : ', design_formats['heading_format_1'])
        # worksheet.write(6, 3, obj.label if obj.label else '', design_formats['heading_format_1'])
        print('-------------------obj.display_type--------------',obj.display_type)
        if obj.sheet_type == 'profit_loss' and obj.show_debit_credit:
            if obj.display_type == 'balance_only':
                worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
                worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
                worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
                
                worksheet.write(9, 3, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 4, 'Credit', design_formats['heading_format_3'])
                
                worksheet.write(9, 5, 'Balance', design_formats['heading_format_3'])
                row = 9
                col = 0
                
                total_debit = 0.0
                total_credit = 0.0
                total_opening_balance = 0.0
                total_closing_balance = 0.0
                
                for line in obj.trial_balance_line_ids:
                    type_label = dict(line._fields['type'].selection).get(line.type)
                    
                    row += 1
                    worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 3,line.debit if line.debit else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 4,line.credit if line.credit else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 5,line.closing_balance if line.closing_balance else '',design_formats['normal_format_right'])
                    
                    total_debit += line.debit
                    total_credit += line.credit
                    total_opening_balance += line.opening_balance
                    total_closing_balance += line.closing_balance
            
                worksheet.write(row+2, col + 3,total_debit, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 4,total_credit,design_formats['normal_format_right'])
                worksheet.write(row+2, col + 5, round(total_closing_balance,2), design_formats['normal_format_right'])
            elif obj.display_type == 'complete':
                worksheet.merge_range('D9:F9', 'Opening', design_formats['heading_format_3'])
                worksheet.merge_range('G9:I9', 'Opening', design_formats['heading_format_3'])
                worksheet.merge_range('J9:L9', 'Opening', design_formats['heading_format_3'])
                
                
                worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
                worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
                worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
                worksheet.write(9, 3, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 4, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 5, 'Balance', design_formats['heading_format_3'])
                worksheet.write(9, 6, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 7, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 8, 'Balance', design_formats['heading_format_3'])
                worksheet.write(9, 9, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 10, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 11, 'Balance', design_formats['heading_format_3'])
                row = 9
                col = 0
                
                total_debit1 = 0
                total_debit2 = 0
                total_debit3 = 0
                
                
                total_credit1 = 0
                total_credit2 = 0
                total_credit3 = 0
                
                total_opening_balance1 = 0
                total_opening_balance2 = 0
                total_opening_balance3 = 0
                
                for line in obj.trial_balance_complete_line_ids:
                    type_label = dict(line._fields['type'].selection).get(line.type)
                    row += 1
                    worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 3, line.debit1 if line.debit1 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 4,line.credit1 if line.credit1 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 5,line.opening_balance1 if line.opening_balance1 else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 6, line.debit2 if line.debit2 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 7,line.credit2 if line.credit2 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 8,line.opening_balance2 if line.opening_balance2 else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 9, line.debit3 if line.debit3 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 10,line.credit3 if line.credit3 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 11,line.opening_balance3 if line.opening_balance3 else '',design_formats['normal_format_right'])
                    
                    total_debit1 += line.debit1
                    total_debit2 += line.debit2
                    total_debit3 += line.debit3
                    
                    
                    total_credit1 += line.credit1
                    total_credit2 += line.credit2
                    total_credit3 += line.credit3
                    
                    total_opening_balance1 += line.opening_balance1
                    total_opening_balance2 += line.opening_balance2
                    total_opening_balance3 += line.opening_balance3
                
                worksheet.write(row+2, col + 3, total_debit1, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 4,total_credit1, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 5,round(total_opening_balance1,2),design_formats['normal_format_right'])
                worksheet.write(row+2, col + 6, total_debit2, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 7,total_credit2, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 8,round(total_opening_balance2,2),design_formats['normal_format_right'])
                worksheet.write(row+2, col + 9, total_debit3, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 10,total_credit3, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 11,round(total_opening_balance3,2),design_formats['normal_format_right'])
        elif obj.sheet_type == 'profit_loss' and not obj.show_debit_credit:
            if obj.display_type == 'balance_only':
                worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
                worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
                worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
                
                
                worksheet.write(9, 3, 'Balance', design_formats['heading_format_3'])
                row = 9
                col = 0
                
                total_debit = 0.0
                total_credit = 0.0
                total_opening_balance = 0.0
                total_closing_balance = 0.0
                
                for line in obj.trial_balance_line_ids:
                    type_label = dict(line._fields['type'].selection).get(line.type)
                    
                    row += 1
                    worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 3,line.closing_balance if line.closing_balance else '',design_formats['normal_format_right'])
                    
                    total_debit += line.debit
                    total_credit += line.credit
                    total_opening_balance += line.opening_balance
                    total_closing_balance += line.closing_balance
            
                worksheet.write(row+2, col + 3, round(total_closing_balance,2), design_formats['normal_format_right'])
            elif obj.display_type == 'complete':
                worksheet.merge_range('D9:F9', 'Opening', design_formats['heading_format_3'])
                worksheet.merge_range('G9:I9', 'Opening', design_formats['heading_format_3'])
                worksheet.merge_range('J9:L9', 'Opening', design_formats['heading_format_3'])
                
                
                worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
                worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
                worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
                worksheet.write(9, 3, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 4, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 5, 'Balance', design_formats['heading_format_3'])
                worksheet.write(9, 6, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 7, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 8, 'Balance', design_formats['heading_format_3'])
                worksheet.write(9, 9, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 10, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 11, 'Balance', design_formats['heading_format_3'])
                row = 9
                col = 0
                
                total_debit1 = 0
                total_debit2 = 0
                total_debit3 = 0
                
                
                total_credit1 = 0
                total_credit2 = 0
                total_credit3 = 0
                
                total_opening_balance1 = 0
                total_opening_balance2 = 0
                total_opening_balance3 = 0
                
                for line in obj.trial_balance_complete_line_ids:
                    type_label = dict(line._fields['type'].selection).get(line.type)
                    row += 1
                    worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 3, line.debit1 if line.debit1 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 4,line.credit1 if line.credit1 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 5,line.opening_balance1 if line.opening_balance1 else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 6, line.debit2 if line.debit2 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 7,line.credit2 if line.credit2 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 8,line.opening_balance2 if line.opening_balance2 else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 9, line.debit3 if line.debit3 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 10,line.credit3 if line.credit3 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 11,line.opening_balance3 if line.opening_balance3 else '',design_formats['normal_format_right'])
                    
                    total_debit1 += line.debit1
                    total_debit2 += line.debit2
                    total_debit3 += line.debit3
                    
                    
                    total_credit1 += line.credit1
                    total_credit2 += line.credit2
                    total_credit3 += line.credit3
                    
                    total_opening_balance1 += line.opening_balance1
                    total_opening_balance2 += line.opening_balance2
                    total_opening_balance3 += line.opening_balance3
                
                worksheet.write(row+2, col + 3, total_debit1, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 4,total_credit1, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 5,round(total_opening_balance1,2),design_formats['normal_format_right'])
                worksheet.write(row+2, col + 6, total_debit2, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 7,total_credit2, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 8,round(total_opening_balance2,2),design_formats['normal_format_right'])
                worksheet.write(row+2, col + 9, total_debit3, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 10,total_credit3, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 11,round(total_opening_balance3,2),design_formats['normal_format_right'])
        else:
            if obj.display_type == 'balance_only':
                worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
                worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
                worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
                
                worksheet.write(8, 3, 'Opening', design_formats['heading_format_3'])
                
                worksheet.write(9, 3, 'Balance', design_formats['heading_format_3'])
                worksheet.merge_range('E9:F9', 'Transactions', design_formats['heading_format_3'])
                worksheet.write(9, 4, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 5, 'Credit', design_formats['heading_format_3'])
                
                worksheet.write(8, 6, 'Closing', design_formats['heading_format_3'])
                worksheet.write(9, 6, 'Balance', design_formats['heading_format_3'])
                row = 9
                col = 0
                
                total_debit = 0.0
                total_credit = 0.0
                total_opening_balance = 0.0
                total_closing_balance = 0.0
                
                for line in obj.trial_balance_line_ids:
                    type_label = dict(line._fields['type'].selection).get(line.type)
                    
                    row += 1
                    worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 3, line.opening_balance if line.opening_balance else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 4,line.debit if line.debit else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 5,line.credit if line.credit else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 6,line.closing_balance if line.closing_balance else '',design_formats['normal_format_right'])
                    
                    total_debit += line.debit
                    total_credit += line.credit
                    total_opening_balance += line.opening_balance
                    total_closing_balance += line.closing_balance
            
                worksheet.write(row+2, col + 3, round(total_opening_balance,2), design_formats['normal_format_right'])
                worksheet.write(row+2, col + 4,total_debit, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 5,total_credit,design_formats['normal_format_right'])
                worksheet.write(row+2, col + 6, round(total_closing_balance,2), design_formats['normal_format_right'])
            elif obj.display_type == 'complete':
                worksheet.merge_range('D9:F9', 'Opening', design_formats['heading_format_3'])
                worksheet.merge_range('G9:I9', 'Opening', design_formats['heading_format_3'])
                worksheet.merge_range('J9:L9', 'Opening', design_formats['heading_format_3'])
                worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
                worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
                worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
                worksheet.write(9, 3, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 4, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 5, 'Balance', design_formats['heading_format_3'])
                worksheet.write(9, 6, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 7, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 8, 'Balance', design_formats['heading_format_3'])
                worksheet.write(9, 9, 'Debit', design_formats['heading_format_3'])
                worksheet.write(9, 10, 'Credit', design_formats['heading_format_3'])
                worksheet.write(9, 11, 'Balance', design_formats['heading_format_3'])
                row = 9
                col = 0
                total_debit1 = 0
                total_debit2 = 0
                total_debit3 = 0
                
                total_credit1 = 0
                total_credit2 = 0
                total_credit3 = 0
                
                total_opening_balance1 = 0
                total_opening_balance2 = 0
                total_opening_balance3 = 0
                
                for line in obj.trial_balance_complete_line_ids:
                    type_label = dict(line._fields['type'].selection).get(line.type)
                    row += 1
                    worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
                    worksheet.write(row, col + 3, line.debit1 if line.debit1 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 4,line.credit1 if line.credit1 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 5,line.opening_balance1 if line.opening_balance1 else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 6, line.debit2 if line.debit2 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 7,line.credit2 if line.credit2 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 8,line.opening_balance2 if line.opening_balance2 else '',design_formats['normal_format_right'])
                    worksheet.write(row, col + 9, line.debit3 if line.debit3 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 10,line.credit3 if line.credit3 else '', design_formats['normal_format_right'])
                    worksheet.write(row, col + 11,line.opening_balance3 if line.opening_balance3 else '',design_formats['normal_format_right'])
                    
                    total_debit1 += line.debit1
                    total_debit2 += line.debit2
                    total_debit3 += line.debit3
                    
                    
                    total_credit1 += line.credit1
                    total_credit2 += line.credit2
                    total_credit3 += line.credit3
                    
                    total_opening_balance1 += line.opening_balance1
                    total_opening_balance2 += line.opening_balance2
                    total_opening_balance3 += line.opening_balance3
                
                worksheet.write(row+2, col + 3, total_debit1, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 4,total_credit1, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 5,round(total_opening_balance1,2),design_formats['normal_format_right'])
                worksheet.write(row+2, col + 6, total_debit2, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 7,total_credit2, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 8,round(total_opening_balance2,2),design_formats['normal_format_right'])
                worksheet.write(row+2, col + 9, total_debit3, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 10,total_credit3, design_formats['normal_format_right'])
                worksheet.write(row+2, col + 11,round(total_opening_balance3,2),design_formats['normal_format_right'])
            sheet_type = fields.Selection(
        selection=[
            ("balance_sheet", "Balance Sheet"),
            ("profit_loss", "Profit & Loss"),
            ("trial_balance", "Trial Balance"),
        ],
        string="Type"
        
    )       
        file_name = 'Trial Balance'
        if obj.sheet_type == 'balance_sheet':
            file_name = 'Balance Sheet'
        elif obj.sheet_type == 'profit_loss':
            file_name = 'Profit Loss'
                
                
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': file_name + '.xlsx'})
        return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xlsx' % (
                    report_id.id, file_name),
                'target': 'new',
            }
        output.close()
            # worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
            # worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
            # worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
            #
            # worksheet.write(8, 3, 'Opening', design_formats['heading_format_3'])
            #
            # worksheet.write(9, 3, 'Balance', design_formats['heading_format_3'])
            # worksheet.merge_range('E9:F9', 'Transactions', design_formats['heading_format_3'])
            # worksheet.write(9, 4, 'Debit', design_formats['heading_format_3'])
            # worksheet.write(9, 5, 'Credit', design_formats['heading_format_3'])
            #
            # worksheet.write(8, 6, 'Closing', design_formats['heading_format_3'])
            # worksheet.write(9, 6, 'Balance', design_formats['heading_format_3'])
            # row = 9
            # col = 0
            #
            # total_debit = 0.0
            # total_credit = 0.0
            # total_opening_balance = 0.0
            # total_closing_balance = 0.0
            # print('-------------------obj.trial_balance_line_ids--------------',obj.trial_balance_line_ids)
            # for line in obj.trial_balance_line_ids:
            #     type_label = dict(line._fields['type'].selection).get(line.type)
            #
            #     row += 1
            #     worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
            #     worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
            #     worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
            #     worksheet.write(row, col + 3, line.opening_balance if line.opening_balance else '', design_formats['normal_format_right'])
            #     worksheet.write(row, col + 4,line.debit if line.debit else '', design_formats['normal_format_right'])
            #     worksheet.write(row, col + 5,line.credit if line.credit else '',design_formats['normal_format_right'])
            #     worksheet.write(row, col + 6,line.closing_balance if line.closing_balance else '',design_formats['normal_format_right'])
            #
            #     total_debit += line.debit
            #     total_credit += line.credit
            #     total_opening_balance += line.opening_balance
            #     total_closing_balance += line.closing_balance
            #
            # worksheet.write(row+2, col + 3, round(total_opening_balance,2), design_formats['normal_format_right'])
            # worksheet.write(row+2, col + 4,total_debit, design_formats['normal_format_right'])
            # worksheet.write(row+2, col + 5,total_credit,design_formats['normal_format_right'])
            # worksheet.write(row+2, col + 6, round(total_closing_balance,2), design_formats['normal_format_right'])

        
        # elif obj.display_type == 'complete':
        #     worksheet.merge_range('D9:F9', 'Opening', design_formats['heading_format_3'])
        #     worksheet.merge_range('G9:I9', 'Opening', design_formats['heading_format_3'])
        #     worksheet.merge_range('J9:L9', 'Opening', design_formats['heading_format_3'])
        #
        #
        #     worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
        #     worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
        #     worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
        #     worksheet.write(9, 3, 'Debit', design_formats['heading_format_3'])
        #     worksheet.write(9, 4, 'Credit', design_formats['heading_format_3'])
        #     worksheet.write(9, 5, 'Balance', design_formats['heading_format_3'])
        #     worksheet.write(9, 6, 'Debit', design_formats['heading_format_3'])
        #     worksheet.write(9, 7, 'Credit', design_formats['heading_format_3'])
        #     worksheet.write(9, 8, 'Balance', design_formats['heading_format_3'])
        #     worksheet.write(9, 9, 'Debit', design_formats['heading_format_3'])
        #     worksheet.write(9, 10, 'Credit', design_formats['heading_format_3'])
        #     worksheet.write(9, 11, 'Balance', design_formats['heading_format_3'])
        #     row = 9
        #     col = 0
        #
        #     total_debit1 = 0
        #     total_debit2 = 0
        #     total_debit3 = 0
        #
        #
        #     total_credit1 = 0
        #     total_credit2 = 0
        #     total_credit3 = 0
        #
        #     total_opening_balance1 = 0
        #     total_opening_balance2 = 0
        #     total_opening_balance3 = 0
        #     print('-------------------obj.trial_balance_complete_line_ids--------------',obj.trial_balance_complete_line_ids)
        #     for line in obj.trial_balance_complete_line_ids:
        #         type_label = dict(line._fields['type'].selection).get(line.type)
        #         row += 1
        #         worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
        #         worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
        #         worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
        #         worksheet.write(row, col + 3, line.debit1 if line.debit1 else '', design_formats['normal_format_right'])
        #         worksheet.write(row, col + 4,line.credit1 if line.credit1 else '', design_formats['normal_format_right'])
        #         worksheet.write(row, col + 5,line.opening_balance1 if line.opening_balance1 else '',design_formats['normal_format_right'])
        #         worksheet.write(row, col + 6, line.debit2 if line.debit2 else '', design_formats['normal_format_right'])
        #         worksheet.write(row, col + 7,line.credit2 if line.credit2 else '', design_formats['normal_format_right'])
        #         worksheet.write(row, col + 8,line.opening_balance2 if line.opening_balance2 else '',design_formats['normal_format_right'])
        #         worksheet.write(row, col + 9, line.debit3 if line.debit3 else '', design_formats['normal_format_right'])
        #         worksheet.write(row, col + 10,line.credit3 if line.credit3 else '', design_formats['normal_format_right'])
        #         worksheet.write(row, col + 11,line.opening_balance3 if line.opening_balance3 else '',design_formats['normal_format_right'])
        #
        #         total_debit1 += line.debit1
        #         total_debit2 += line.debit2
        #         total_debit3 += line.debit3
        #
        #
        #         total_credit1 += line.credit1
        #         total_credit2 += line.credit2
        #         total_credit3 += line.credit3
        #
        #         total_opening_balance1 += line.opening_balance1
        #         total_opening_balance2 += line.opening_balance2
        #         total_opening_balance3 += line.opening_balance3
        #
        #     worksheet.write(row+2, col + 3, total_debit1, design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 4,total_credit1, design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 5,round(total_opening_balance1,2),design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 6, total_debit2, design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 7,total_credit2, design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 8,round(total_opening_balance2,2),design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 9, total_debit3, design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 10,total_credit3, design_formats['normal_format_right'])
        #     worksheet.write(row+2, col + 11,round(total_opening_balance3,2),design_formats['normal_format_right'])
        # workbook.close()
        # output.seek(0)
        # result = base64.b64encode(output.read())
        # report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'Trial Balance.xlsx'})
        #
        # return {
        #         'type': 'ir.actions.act_url',
        #         'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xlsx' % (
        #             report_id.id, 'Trial Balance'),
        #         'target': 'new',
        #     }
        # output.close()
                
    # def print_xlsx(self):
    #     # products = self.mapped('order_line.product_id.name')
    #     return self.env.ref('zb_financial_reports.trial_balance_xlsx_report').report_action(self)
        
    
class TrialBalanceWizardLine(models.TransientModel):
    _name = 'trial.balance.wiz.line'
    _description = 'Trial Balance Line Wizard'
    
    
    name = fields.Char('Account Name')
    code = fields.Char('Account Code')
    type = fields.Selection(
        selection=[
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("expense", "Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),
            ("off_balance", "Off-Balance Sheet"),
        ],
        string="Type")
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    opening_balance = fields.Float(string='Opening Balance')
    closing_balance = fields.Float(string='Closing Balance')
    
    trial_balance_id = fields.Many2one('trial.balance.wiz', string='Trial Balance Wizard')
    # date = fields.Date('Date')
    # ref = fields.Char('Reference')
    # label = fields.Char("Label")
    account_id = fields.Many2one('account.account', 'Account')
    # partner_id = fields.Many2one('res.partner', 'Partner')
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    # amount_currency = fields.Float(string='Amount Currency')
    currency_id = fields.Many2one('res.currency', string='Currency')
    project_id = fields.Many2one('account.analytic.account', string='Project')
    company = fields.Char(string='Company',

    )
    company_id = fields.Many2one('res.company',string='Company',
        
    )
    # company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    
    # balance = fields.Float(string='Balance')
    # balance_currency = fields.Float(string='Balance Currency')
    
    def open_general_ledger(self):
        for rec in self:
            domain = [('parent_state','=','posted')]
            # if rec.trial_balance_id.from_date:
            #     domain.append(('date','>=',rec.trial_balance_id.from_date))
            # if rec.trial_balance_id.to_date:
            #     domain.append(('date','<=',rec.trial_balance_id.to_date))
            if rec.account_id:
                domain.append(('account_id','=',rec.account_id.id))
            if rec.type:
                if rec.type == 'asset_receivable':
                    domain.append(('account_type','=','asset_receivable'))
                elif rec.type == 'liability_payable':
                    domain.append(('account_type','=','liability_payable'))
            if self.env.company:
                company_ids = self.env['res.company'].search([('parent_id', '=', self.env.company.id)])
                if company_ids:
                    domain.append('|')
                    domain.append(('company_id', '=', self.env.company.id))
                    domain.append(('company_id', 'in', company_ids.ids))
                else:
                    domain.append(('company_id', '=', self.env.company.id))
                    
            # line_ids = self.env['account.move.line'].search(domain,order='date asc,id asc')
            # partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
            # account_ids = set(self.env['account.move.line'].search(domain).mapped('account_id'))
                
            if rec.account_id.account_type in ['asset_receivable','liability_payable']:
                partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
                if rec.trial_balance_id.to_date:
                    domain.append(('date', '<=', rec.trial_balance_id.to_date))
                account_ids = set(self.env['account.move.line'].search(domain).mapped('account_id'))
                if rec.trial_balance_id.from_date:
                    domain.append(('date', '>=', rec.trial_balance_id.from_date))
                line_ids = self.env['account.move.line'].search(domain, order='date asc, id asc')
                line_list = []
                for partner in partner_ids:
                    opening_balance = sum(self.env['account.move.line'].search([
                        ('partner_id','=',partner.id),
                        ('date','<',rec.trial_balance_id.from_date),
                        ('parent_state','=','posted'),
                        ('account_id','=',rec.account_id.id)
                    ]).mapped('debit')) - sum(self.env['account.move.line'].search([
                            ('partner_id','=',partner.id),
                            ('date','<',rec.trial_balance_id.from_date),
                            ('parent_state','=','posted'),
                            ('account_id','=',rec.account_id.id)
                    ]).mapped('credit'))
                    
                    debit = sum(self.env['account.move.line'].search([
                        ('partner_id','=',partner.id),
                        ('date','>=',rec.trial_balance_id.from_date),
                        ('date','<=',rec.trial_balance_id.to_date),
                        ('parent_state','=','posted'),
                        ('account_id','=',rec.account_id.id)
                    ]).mapped('debit')) 
                    credit = sum(self.env['account.move.line'].search([
                        ('partner_id','=',partner.id),
                        ('date','>=',rec.trial_balance_id.from_date),
                        ('date','<=',rec.trial_balance_id.to_date),
                        ('parent_state','=','posted'),
                        ('account_id','=',rec.account_id.id)
                    ]).mapped('credit'))
                    closing_balance = opening_balance + (debit - credit)
                    balance_currency = sum(self.env['account.move.line'].search([
                        ('partner_id','=',partner.id),
                        ('date','>=',rec.trial_balance_id.from_date),
                        ('date','<=',rec.trial_balance_id.to_date),
                        ('parent_state','=','posted'),
                        ('account_id','=',rec.account_id.id)
                    ]).mapped('amount_currency'))
                    
                    vals = {
                                'name': partner.display_name,
                                'partner_id': partner.id,
                                'debit': debit,
                                'credit': credit,
                                'opening_balance': opening_balance,
                                'closing_balance' : closing_balance,
                                'balance_currency' : balance_currency
                                }
                    line_list.append((0, 0, vals))
                    # opening_balance = opening_balance + (line.debit-line.credit)
                    # opening_balance_currency = opening_balance_currency + line.amount_currency
                    
                    
                partner_summary_wiz = self.env['partner.summary.wiz'].create({
                    'from_date': rec.trial_balance_id.from_date,
                    'to_date': rec.trial_balance_id.to_date,
                    'account_type': False,
                    'account_ids': [(6, 0, [rec.account_id.id])],
                    'partner_summary_line_ids': line_list,
                    #'load_data_on_open': True,
                })
                
                
                
                
                return {
                    'name': _('Partner Summary'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'partner.summary.wiz',
                    'res_id': partner_summary_wiz.id,
                }
            
            else:
                if rec.trial_balance_id.to_date:
                    domain.append(('date', '<=', rec.trial_balance_id.to_date))
                account_ids = set(self.env['account.move.line'].search(domain).mapped('account_id'))
                if rec.trial_balance_id.from_date:
                    domain.append(('date', '>=', rec.trial_balance_id.from_date))
                partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
                line_ids = self.env['account.move.line'].search(domain, order='date asc, id asc')
                line_list = []
                for account in account_ids:
                    opening_balance = sum(self.env['account.move.line'].search([
                        ('account_id','=',account.id),
                        ('date','<',rec.trial_balance_id.from_date),
                        ('parent_state','=','posted')
                    ]).mapped('debit')) - sum(self.env['account.move.line'].search([
                        ('account_id','=',account.id),
                        ('date','<',rec.trial_balance_id.from_date),
                        ('parent_state','=','posted')
                    ]).mapped('credit'))
                    
                    opening_balance_currency = sum(self.env['account.move.line'].search([
                        ('account_id','=',account.id),
                        ('date','<',rec.trial_balance_id.from_date),
                        ('parent_state','=','posted')
                    ]).mapped('amount_currency'))
                    if opening_balance:
                        line_list.append((0, 0, {'name': account.display_name, 'ref': 'Opening Balance', 'balance': opening_balance, 'balance_currency': opening_balance_currency}))
                    for line in line_ids:
                        if line.account_id == account:
                            vals = {
                                # 'move_line_id': line.move_line_id.id,
                                        'date': line.date,
                                        'ref': line.move_id.name,
                                        'label': line.name,
                                        'account_id': line.account_id.id,
                                        'partner_id': line.partner_id.id,
                                        # 'analytic_account_id': line.analytic_account_id.id,
                                        'amount_currency': line.amount_currency,
                                        'currency_id': line.currency_id.id,
                                        'move_line_id' : line.id,
                                        'debit': line.debit,
                                        'credit': line.credit,
                                        'balance': opening_balance + (line.debit-line.credit),
                                        'balance_currency' : opening_balance_currency + line.amount_currency
                                        }
                            line_list.append((0, 0, vals))
                            opening_balance = opening_balance + (line.debit-line.credit)
                            opening_balance_currency = opening_balance_currency + line.amount_currency
                
                
                
                
                
                
                general_ledger_wiz = self.env['general.ledger.wiz'].create({
                    'from_date': rec.trial_balance_id.from_date,
                    'to_date': rec.trial_balance_id.to_date,
                    'account_ids': [(6, 0, [rec.account_id.id])],
                    'analytic_account_id': rec.project_id.id,
                    'general_ledger_line_ids': line_list,
                    #'load_ledger_data_on_open': True,
                })
                
                return {
                    'name': _('General Ledger'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'general.ledger.wiz',
                    'res_id': general_ledger_wiz.id,
                }
            
            
class TrialBalanceWizardCompleteLine(models.TransientModel):
    _name = 'trial.balance.wiz.complete.line'
    _description = 'Trial Balance Wizard'
    
    name = fields.Char('Account Name')
    code = fields.Char('Account Code')
    type = fields.Selection(
        selection=[
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("expense", "Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_direct_cost", "Cost of Revenue"),
            ("off_balance", "Off-Balance Sheet"),
        ],
        string="Type")
    debit1 = fields.Float(string='Debit')
    credit1 = fields.Float(string='Credit')
    opening_balance1 = fields.Float(string='Balance')
    debit2 = fields.Float(string='Debit')
    credit2 = fields.Float(string='Credit')
    opening_balance2 = fields.Float(string='Balance')
    debit3 = fields.Float(string='Debit')
    credit3 = fields.Float(string='Credit')
    opening_balance3 = fields.Float(string='Balance')
    trial_balance_id = fields.Many2one('trial.balance.wiz', string='Trial Balance Wizard')
    account_id = fields.Many2one('account.account', 'Account')
    currency_id = fields.Many2one('res.currency', string='Currency')
    project_id = fields.Many2one('account.analytic.account', string='Project')
    company = fields.Char(string='Company',
        
    )
    company_id = fields.Many2one('res.company',string='Company',
        
    )
    
