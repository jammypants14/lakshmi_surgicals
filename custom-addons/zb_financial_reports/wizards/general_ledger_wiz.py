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
from odoo import fields, models,api,_
from odoo.exceptions import ValidationError,UserError
import base64
import datetime
from datetime import date, timedelta

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class GeneralLedgerWizard(models.TransientModel):

    _name = 'general.ledger.wiz'
    _description = 'General Ledger Wizard'
    
    name = fields.Char('Name',default = 'General Ledger')
    general_ledger_line_ids = fields.One2many('general.ledger.wiz.line', 'general_ledger_id', string='General Ledger Wizard Lines')
    from_date = fields.Date('From Date',default=lambda self: date.today() - timedelta(days=30))
    to_date = fields.Date('To Date',default=fields.Date.context_today)
    account_ids = fields.Many2many('account.account','ledger_account_rel','ledg_id','acc_id','Account(s)')
    partner_ids = fields.Many2many('res.partner','ledger_partner_rel','ledg_vend_id','vend_id','Partner(s)')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    label = fields.Char("Label")
    group_by = fields.Selection([('account','Account'),('partner','Partner')])
    
    # currency_id = fields.Many2one('res.currency',string='Currency')
    company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    # amount = fields.Monetary(string='Amount', currency_field='company_currency_id')
    is_foreign_currency = fields.Boolean(string='Foreign Currency')
    show_draft = fields.Boolean(string='Show Draft Also')
    search_field=fields.Char("Search")
    
    company_id=fields.Many2one("res.company", default=lambda self: self.env.company.id)
    child_company_ids=fields.Many2many("res.company","company_general_rel","company_id","general_ledger_id",string="Child Company")

    @api.onchange('company_id')  
    def onchange_company_id(self):
        for rec in self:
            list1=[(5,0,0)] 
            for child in rec.company_id.child_ids:
                list1.append(child)                       
            rec.child_company_ids=[(6,0,rec.company_id.child_ids.ids)]  
            
    @api.onchange('search_field')  
    def onchange_search(self):              
        for rec in self:
            print("=====rec.partner_ledger_line_ids======",rec.general_ledger_line_ids)
            line_list=[]
            for line in rec.general_ledger_line_ids:
                
                
                if(line.ref==rec.search_field
                    or line.label==rec.search_field
                    or line.analytic_account_id.name==rec.search_field):
                    pass
                else:
                    print("=====line========",line)
                    line_list.append(line)
            for line in line_list:
                line.unlink()
    
    
    def load_data(self):
        # analytic_fields = self.env['ir.model.fields'].search([('model_id.model','=','account.analytic.line'),('relation','=','account.analytic.account')])
        for rec in self:
            rec.general_ledger_line_ids = False
            if rec.show_draft == True:
                domain = [('parent_state','in',['posted','draft'])]
            else:
                domain = [('parent_state', '=', 'posted')]
            
            # if self.env.company:
            #     company_ids = self.env['res.company'].search([('parent_id','=',self.env.company.id)])
            #     if company_ids:
            #         domain.append('|')
            #         domain.append(('company_id','=',self.env.company.id))
            #         domain.append(('company_id','in',company_ids.ids))
            #     else:
            #         domain.append(('company_id','=',self.env.company.id))
            company_ids = self.env.context.get('allowed_company_ids',[])
            if self.env.user.has_group('account.group_account_manager'):
                if company_ids:
                    # domain.append('|')
                    domain.append(('company_id','in',company_ids))
                else:
                    domain.append(('company_id','=',rec.company_id.id))
            else:
                domain.append(('company_id','=',rec.company_id.id))    
            print("domain",domain)
            if rec.to_date:
                domain.append(('date','<=',rec.to_date))
            if rec.analytic_account_id:
                domain.append(('analytic_account_id','=',rec.analytic_account_id.id))
            if rec.account_ids:
                domain.append(('account_id','in',rec.account_ids.ids))
            
            if rec.partner_ids:
                domain.append(('partner_id','in',rec.partner_ids.ids))
            
            account_ids = set(self.env['account.move.line'].search(domain).mapped('account_id'))
            if rec.from_date:
                domain.append(('date','>=',rec.from_date))
            line_ids = self.env['account.move.line'].search(domain,order='date asc,id asc')
            partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
            
            # if rec.group_by == 'account':
            line_list = []
            for account in account_ids:
                opening_balance = sum(self.env['account.move.line'].search([('account_id','=',account.id),('date','<',rec.from_date),('parent_state','=','posted')]).mapped('debit')) - sum(self.env['account.move.line'].search([('account_id','=',account.id),('date','<',rec.from_date),('parent_state','=','posted')]).mapped('credit'))
                
                opening_balance_currency = sum(self.env['account.move.line'].search([('account_id','=',account.id),('date','<',rec.from_date),('parent_state','=','posted')]).mapped('amount_currency'))
                if account.account_type not in ['income','other_income','expense_depreciation','expense_direct_cost','expense']:
                    line_list.append((0, 0, {'name':account.display_name,'ref':'Opening Balance','balance':opening_balance,'balance_currency':opening_balance_currency}))
                else:
                    line_list.append((0, 0, {'name':account.display_name}))
                for line in line_ids:
                    
                    
                    # for analytic_line in line.analytic_line_ids:
                    #     for analytic_field in analytic_fields:
                    #         print("analytic_field================",analytic_field)
                    #         print("analytic_line===============",analytic_line)
                    #         print("value================",analytic_line.analytic_field)
                    
                    
                    
                    if line.account_id == account:
                        move_lines = self.env['account.move.line'].search([('move_id','=',line.move_id.id)])
                        move_lines_without_current = self.env['account.move.line'].search([('move_id','=',line.move_id.id),('account_id','!=',line.account_id.id)])
                        counter_account = ''
                        if move_lines and len(move_lines) <= 2:
                            counter_account = move_lines_without_current.account_id.display_name
                        else:
                            counter_account = line.move_id.journal_id.name
                        vals = {
                            # 'move_line_id': line.move_line_id.id,
                                    'date': line.date,
                                    'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
                                    'label': line.name,
                                    'account_id': line.account_id.id,
                                    'counter_account' : counter_account,
                                    'partner_id': line.partner_id.id,
                                    'analytic_account_id': line.analytic_account_id.id,
                                    'amount_currency': line.amount_currency,
                                    'currency_id': line.currency_id.id,
                                    'move_line_id' : line.id,
                                    'debit': line.debit,
                                    'credit': line.credit,
                                    'balance': opening_balance + (line.debit-line.credit),
                                    'balance_currency' : opening_balance_currency + line.amount_currency,
                                     'journal_id': line.journal_id.id,
                                    }
                        line_list.append((0, 0, vals))
                        opening_balance = opening_balance + (line.debit-line.credit)
                        opening_balance_currency = opening_balance_currency + line.amount_currency
            
            
            rec.general_ledger_line_ids = line_list
                
    def print_general_ledger_xlsx(self):
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
            worksheet.merge_range('F1:H1', company_name, design_formats['heading_format_2'])
            worksheet.merge_range('F2:H2', 'General Ledger', design_formats['heading_format_2'])
            worksheet.merge_range('F2:H2', 'General Ledger', design_formats['heading_format_2'])
            
            worksheet.write(4, 0, 'From Date : ', design_formats['heading_format_1'])
            worksheet.write(4, 1, obj.from_date if obj.from_date else '', design_formats['date_format'])
            worksheet.write(5, 0, 'To Date : ', design_formats['heading_format_1'])
            worksheet.write(5, 1, obj.to_date if obj.to_date else '', design_formats['date_format'])
            
            worksheet.write(6, 0, 'Account(s) : ', design_formats['heading_format_1'])
            account_name = ''
            if obj.account_ids:
                for account in obj.account_ids:
                    account_name += account.display_name + ','
            worksheet.write(6, 1, account_name, design_formats['normal_format_central'])
            
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
            
        for line in obj.general_ledger_line_ids:
            row += 1
            worksheet.write(row, col, line.name if line.name else '', design_formats['normal_format_left'])
            worksheet.write(row, col + 1, line.date if line.date else '', design_formats['date_format'])
            worksheet.write(row, col + 2, line.ref if line.ref else '', design_formats['normal_format_central'])
            worksheet.write(row, col + 3, line.label if line.label else '', design_formats['normal_format_central'])
            worksheet.write(row, col + 4, line.counter_account if line.counter_account else '', design_formats['normal_format_central'])
            worksheet.write(row, col + 5, line.partner_id.name if line.partner_id else '', design_formats['normal_format_central'])
            worksheet.write(row, col + 6, line.analytic_account_id.name if line.analytic_account_id else '', design_formats['normal_format_central'])
            if obj.is_foreign_currency:
                worksheet.write(row, col + 7, line.amount_currency if line.amount_currency else '', design_formats['normal_format_right'])
                worksheet.write(row, col + 8, line.currency_id.name if line.currency_id else '', design_formats['normal_format_central'])
                worksheet.write(row, col + 9, line.debit, design_formats['normal_format_right'])
                worksheet.write(row, col + 10, line.credit, design_formats['normal_format_right'])
                worksheet.write(row, col + 11, line.balance, design_formats['normal_format_right'])
                worksheet.write(row, col + 12, line.balance_currency, design_formats['normal_format_right'])
            else:
                worksheet.write(row, col + 7, line.debit, design_formats['normal_format_right'])
                worksheet.write(row, col + 8, line.credit, design_formats['normal_format_right'])
                worksheet.write(row, col + 9, line.balance, design_formats['normal_format_right'])
                    
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'General ledger Report.xlsx'})
                
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xlsx' % (
                report_id.id, 'General Ledger'),
            'target': 'new',
        }
        output.close()                   
       
    # def print_xlsx(self):
    #     # products = self.mapped('order_line.product_id.name')
    #     return self.env.ref('zb_financial_reports.general_ledger_xlsx_report').report_action(self)
    #

        
    
class GeneralLedgerWizardLine(models.TransientModel):
    _name = 'general.ledger.wiz.line'
    _description = 'General Ledger line Wizard'
    
    
    name = fields.Char('Name')
    general_ledger_id = fields.Many2one('general.ledger.wiz', string='General Ledger Wizard')
    move_line_id = fields.Many2one('account.move.line', string='Move Line')
    
    date = fields.Date('Date')
    ref = fields.Char('Reference')
    label = fields.Char("Label")
    account_id = fields.Many2one('account.account','Main Account')
    partner_id = fields.Many2one('res.partner','Partner')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    amount_currency = fields.Float(string='Amount Currency')
    currency_id = fields.Many2one('res.currency',string='Currency')
    # company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')
    balance = fields.Float(string='Balance')
    balance_currency = fields.Float(string='Balance Currency')
    counter_account = fields.Char("Account")
    journal_id = fields.Many2one('account.journal', string='Journal')
    
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
        
        
