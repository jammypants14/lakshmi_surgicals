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
from datetime import datetime, timedelta


try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class DayBookWizard(models.TransientModel):

    _name = 'day.book.wiz'
    _description = 'Day Book Wizard'
    
    name = fields.Char('Name',default = 'Day Book')
    day_book_line_ids = fields.One2many('day.book.wiz.line', 'day_book_id', string='Day Book Wizard Lines')
    from_date = fields.Date(default=lambda self: self._get_yesterday_date(),string="From Date")
    to_date = fields.Date(default=lambda self: self._get_yesterday_date(),string="To Date")
    account_ids = fields.Many2many('account.account','day_account_rel','ledg_id','acc_id','Account(s)',domain="[('account_type', '=', 'asset_cash')]",default=lambda self: self._default_account_ids(),required=True)
    partner_ids = fields.Many2many('res.partner','day_partner_rel','day_vend_id','vend_id','Partner(s)')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    label = fields.Char("Label")
    group_by = fields.Selection([('account','Account'),('partner','Partner')])
    company_id=fields.Many2one("res.company", default=lambda self: self.env.company.id)
    child_company_ids=fields.Many2many("res.company","company_day_book_rel","company_id","day_book_id",string="Child Company")
    
    # currency_id = fields.Many2one('res.currency',string='Currency')
    company_currency_id = fields.Many2one('res.currency',string='Company Currency',default=lambda self: self.env.user.company_id.currency_id.id)
    # amount = fields.Monetary(string='Amount', currency_field='company_currency_id')
    is_foreign_currency = fields.Boolean(string='Foreign Currency')
    # show_draft = fields.Boolean(string='Show Draft Also')
    # search_field=fields.Char("Search")
    
    
    @api.model
    def _default_account_ids(self):
        accounts = self.env['account.account'].search([
            ('account_type', '=', 'asset_cash'),
            ('company_ids', 'in', self.env.company.id)
        ]).ids
        print('---------------------accounts-----------------',accounts)
        return accounts
    
    
    @api.model
    def _get_yesterday_date(self):
        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.date()
    
    # @api.onchange('search_field')  
    # def onchange_search(self):              
    #     for rec in self:
    #         print("=====rec.partner_ledger_line_ids======",rec.day_book_line_ids)
    #         line_list=[]
    #         for line in rec.day_book_line_ids:
    #
    #
    #             if(line.ref==rec.search_field or line.origin==rec.search_field
    #                 or line.vendor_bill==rec.search_field or line.label==rec.search_field
    #                 or line.analytic_account_id.name==rec.search_field):
    #                 pass
    #             else:
    #                 print("=====line========",line)
    #                 line_list.append(line)
    #         for line in line_list:
    #             line.unlink()
    
    
    def load_data(self):
        # analytic_fields = self.env['ir.model.fields'].search([('model_id.model','=','account.analytic.line'),('relation','=','account.analytic.account')])
        for rec in self:
            rec.day_book_line_ids = False
            # if rec.show_draft == True:
            #     domain = [('parent_state','in',['posted','draft'])]
            # else:
            domain = [('parent_state', '=', 'posted')]
            
            # if self.env.company:
            #     company_ids = self.env['res.company'].search([('parent_id','=',self.env.company.id)])
            # company_id = 
            #     if company_ids:
            #         domain.append('|')
            #         domain.append(('company_id','=',self.env.company.id))
            #         domain.append(('company_id','in',company_ids.ids))
            #     else:
            # if rec.company_id:
            #     domain.append(('company_id','=',rec.company_id.id))
            company_ids = self.env.context.get('allowed_company_ids',[])
            if self.env.user.has_group('account.group_account_manager'):
                if company_ids:
                    # domain.append('|')
                    domain.append(('company_id','in',company_ids))
                else:
                    domain.append(('company_id','=',rec.company_id.id))
            else:
                domain.append(('company_id','=',rec.company_id.id))  
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
                                    }
                        line_list.append((0, 0, vals))
                        
                        
                        opening_balance = opening_balance + (line.debit-line.credit)
                        opening_balance_currency = opening_balance_currency + line.amount_currency
            
            print("ookokokokokokokokokookokokokokokokokokokok",line_list)
            rec.day_book_line_ids = line_list
                
    def print_daybook_xlsx(self):
         for obj in self:
            data = self.read()[0]
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            report_name = obj.name
            worksheet = workbook.add_worksheet(report_name[:31])
            design_formats = {'heading_format': workbook.add_format({'align': 'center',
                                                                 'valign': 'vcenter',
                                                                 'bold': True, 'size': 18,
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
                                                                   'bg_color': '#FFFF00',
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
                                                                    'align': 'right', 'size': 11,
                                                                    'text_wrap': True,
                                                                    'border': False, }),
                          'float_bold_format': workbook.add_format({'num_format': '###0.00',
                                                                    'font_name': 'Times New Roman',
                                                                    'align': 'right', 'size': 11,
                                                                    'text_wrap': True,
                                                                    'bold': True,
                                                                    'border': False, }),
                          'float_bold_colour_format': workbook.add_format({'num_format': '###0.00',
                                                                    'font_name': 'Times New Roman',
                                                                    'align': 'right', 'size': 11,
                                                                    'text_wrap': True,
                                                                    'bold': True,
                                                                    'bg_color': '#FFFF00',
                                                                    'border': False, }),
                          'int_rate_format': workbook.add_format({'num_format': '###0',
                                                                  'font_name': 'Times New Roman',
                                                                  'align': 'right', 'size': 11,
                                                                  'text_wrap': True}),
                                                                  
                         'coloured_text_left': workbook.add_format({'align': 'left',
                                                                   'valign': 'vjustify',
                                                                   'bold': True, 'size': 11,
                                                                   'font_name': 'Times New Roman',
                                                                   'color': 'black',
                                                                   'border': False,
                                                                   'bg_color': '#FFFF00',
                                                                   'text_wrap': True, 'shrink': True}),
                                                                    
                                                                    }
            worksheet.set_column('A:A', 1)
            worksheet.set_column('B:B', 9)
            worksheet.set_column('C:C', 50)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 9)
            worksheet.set_column('F:F', 50)
            worksheet.set_column('G:G', 15)
            # current_year = datetime.date.today().strftime("%Y")
            # current_month = datetime.date.today().strftime("%B")
            company_name = self.env.company.name
            worksheet.merge_range('A1:G1', 'DAY BOOK', design_formats['heading_format'])
            worksheet.write(2, 1, 'sl#', design_formats['heading_format_1'])
            worksheet.write(2, 2, 'Reciept', design_formats['heading_format_1'])
            worksheet.write(2, 3, 'amount', design_formats['heading_format_1'])
            worksheet.write(2, 4, 'sl#', design_formats['heading_format_1'])
            worksheet.write(2, 5, 'Payment', design_formats['heading_format_1'])
            worksheet.write(2, 6, 'Payment Value', design_formats['heading_format_1'])
            credit_list=[]
            debit_list=[]
            rows = row = 3
            col = 1
            credit_total = debit_total = 0
            last_closing = total_opening = last_debit = last_credit = 0
            for line in obj.day_book_line_ids:
                if line.name:
                    
                    if debit_total:
                        worksheet.write(row+2, col+1, '*** TOTAL ***', design_formats['heading_format_1'])
                        worksheet.write(row+2, col+2, debit_total, design_formats['float_bold_format'])
                        last_debit = last_debit + debit_total
                        
                        row += 5
                    if credit_total:
                        worksheet.write(rows+2, col+4, '*** TOTAL ***', design_formats['heading_format_1'])
                        worksheet.write(rows+2, col+5, credit_total, design_formats['float_bold_format'])
                        last_credit = last_credit + credit_total
                    closing = debit_total - credit_total
                    if closing:
                        worksheet.write(rows+4, col+4, 'Closing Balance', design_formats['heading_format_1'])
                        worksheet.write(rows+4, col+5, closing, design_formats['float_bold_format'])
                        rows += 5
                        last_closing = last_closing + closing
                    
                    credit_total = debit_total = 0
                    i=0
                    j=0
                    i+=1
                    print(rows,row)
                    if row < rows:
                        row=rows
                    worksheet.merge_range(row, col,row, col+5, line.name if line.name else '', design_formats['heading_format_2'])
                    worksheet.write(row+1, col, i , design_formats['normal_format_right'])
                    worksheet.write(row+1, col+1, line.ref if line.ref else '', design_formats['normal_format_left'])
                    worksheet.write(row+1, col+2, line.balance if line.balance else '', design_formats['float_format'])
                    debit_total = debit_total + line.balance
                    rows = row
                    row+=1
                    total_opening += line.balance
                    print(line.name,row,rows)
                else:
                    if line.debit:
                        i+=1
                        worksheet.write(row+1, col, i , design_formats['normal_format_right'])
                        worksheet.write(row+1, col+1, line.partner_id.name if line.partner_id else (line.label if line.label else (line.ref if line.ref else '')), design_formats['normal_format_left'])
                        worksheet.write(row+1, col+2, line.debit if line.debit else '', design_formats['float_format'])
                        debit_total = debit_total + line.debit
                        row+=1
                    elif line.credit:
                        j+=1
                        worksheet.write(rows+1, col+3, j , design_formats['normal_format_right'])
                        worksheet.write(rows+1, col+4, line.partner_id.name if line.partner_id else (line.label if line.label else (line.ref if line.ref else '')), design_formats['normal_format_left'])
                        worksheet.write(rows+1, col+5, line.credit if line.credit else '', design_formats['float_format'])
                        credit_total = credit_total + line.credit
                        rows+=1
            closing = debit_total - credit_total
            if rows > row:
                row = rows
            if debit_total:
                worksheet.write(row+2, col+1, '*** TOTAL ***', design_formats['heading_format_1'])
                worksheet.write(row+2, col+2, debit_total, design_formats['float_bold_format'])
                last_debit = last_debit + debit_total
                # row += 5  
            print(row,rows)
            if credit_total:
                rows +=1
                worksheet.write(row+2, col+4, '*** TOTAL ***', design_formats['heading_format_1'])
                worksheet.write(row+2, col+5, credit_total, design_formats['float_bold_format'])
                last_credit = last_credit + credit_total
                
            if closing:
                worksheet.write(rows+4, col+4, 'Closing Balance', design_formats['heading_format_1'])
                worksheet.write(rows+4, col+5, closing, design_formats['float_bold_format'])
                row += 5
                
                last_closing = last_closing + closing
            print(rows,row)
            # if row > rows:
            #     rows = row
            worksheet.merge_range(row+3, 1 ,row+3, col+2, 'Summary', design_formats['heading_format'])
            formatted_date = (obj.from_date - timedelta(days=1)).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
            text_with_date = f"Closing Balance As On {formatted_date}"
            worksheet.write(row + 4, col + 1, text_with_date, design_formats['heading_format_1'])
            worksheet.write(row+4, col+2, total_opening, design_formats['float_bold_format'])
            formatted_date = (obj.to_date).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
            text_with_date = f"Total Receipts As On {formatted_date}"
            worksheet.write(row+5, col+1, text_with_date, design_formats['heading_format_1'])
            worksheet.write(row+5, col+2, last_debit, design_formats['float_bold_format'])
            formatted_date = (obj.to_date).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
            text_with_date = f"Total Payments As On {formatted_date}"
            worksheet.write(row+6, col+1, text_with_date, design_formats['heading_format_1'])
            worksheet.write(row+6, col+2, last_credit, design_formats['float_bold_format'])
            formatted_date = (obj.to_date).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
            text_with_date = f"Closing Balance As On {formatted_date}"
            worksheet.write(row + 7, col + 1, text_with_date, design_formats['coloured_text_left'])
            worksheet.write(row+7, col+2, last_closing, design_formats['float_bold_colour_format'])
            workbook.close()
            output.seek(0)
            result = base64.b64encode(output.read())
            report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'Day Book.xlsx'})
        
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xlsx' % (
                    report_id.id, 'Day Book'),
                'target': 'new',
            }
            output.close()
                    
        
    
class DayBookWizLine(models.TransientModel):
    _name = 'day.book.wiz.line'
    _description = 'Day Book line Wizard'
    
    
    name = fields.Char('Name')
    day_book_id = fields.Many2one('day.book.wiz', string='Day Book Wizard')
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
        
        
