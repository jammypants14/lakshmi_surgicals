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
from _datetime import datetime,date
from datetime import timedelta
import json
import io
from odoo.tools import date_utils
import base64

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

from odoo import fields, models,api,_
from odoo.exceptions import ValidationError,UserError

class PartnerLedgerReportWiz(models.TransientModel):
    _name = 'partner.ledger.report.wiz'
    _description = 'Partner Ledger Report Wizard'

    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    account_type = fields.Selection([
        ('asset_receivable', 'Receivable'),
        ('liability_payable', 'Payable'),
        ('receivable_payable', 'Receivable & Payable')
    ], default='receivable_payable', required=True)
    account_ids = fields.Many2many(
        'account.account',
        default=lambda self: self._get_default_accounts()
    )
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    label = fields.Char("Label")
    group_by = fields.Selection([('partner', 'Partner')], default='partner')
    is_foreign_currency = fields.Boolean(string='Foreign Currency')
    show_draft = fields.Boolean(string='Show Draft Also')
    outstanding_only = fields.Boolean(string='Outstanding Only')
    search_field = fields.Char("Search")
    partner_id = fields.Many2one('res.partner', string="Partner")
    partner_ids = fields.Many2many('res.partner')
    
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
            
                rec.account_ids = [(6,0,account_ids.ids)]

    def _get_default_accounts(self):
        """ Get default account IDs for receivable and payable. """
        return self.env['account.account'].search([
            ('account_type', 'in', ['asset_receivable', 'liability_payable'])
        ]).ids

    def _fetch_ledger_data(self):
        """ Fetch partner ledger data. """
        ledger_data = []
        
        opening_balance = self._compute_opening_balance()
        cumulative_balance = opening_balance
        transactions = []

        address = {
            'street': self.partner_id.street,
            'city': self.partner_id.city,
            'zip': self.partner_id.zip,
            'country': self.partner_id.country_id.name if self.partner_id.country_id else '',
        }

        domain = [
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
            ('partner_id', '=', self.partner_id.id),
            ('account_id', 'in', self.account_ids.ids)
        ]
        if not self.show_draft:
            domain.append(('move_id.state', '=', 'posted'))
        
        salesperson_name = ''
        first_move_line = self.env['account.move.line'].search(domain, limit=1)
        if first_move_line and first_move_line.move_id.invoice_user_id:
            salesperson_name = first_move_line.move_id.invoice_user_id.name

        move_lines = self.env['account.move.line'].search(domain, order='date')

        for line in move_lines:
            debit = line.debit
            credit = line.credit
            cumulative_balance += debit - credit
            transactions.append({
                'date': line.date,
                'doc_no': line.move_id.name,
                'detail': f"{line.move_id.name or ''}-{line.move_id.ref or ''} [{line.date.strftime('%d/%m/%y') if line.date else ''}]",
                'debit': debit,
                'credit': credit,
                'balance': cumulative_balance,
            })

        ledger_data.append({
            'partner': self.partner_id,
            'address': address,
            'salesperson': salesperson_name,
            'opening_balance': opening_balance,
            'transactions': transactions,
            'closing_balance': cumulative_balance,
        })
        print("=======================ledger_data==============================================",ledger_data)
        return ledger_data

    def _compute_opening_balance(self):
        """ Compute opening balance for the partner. """
        opening_domain = [
            ('date', '<', self.from_date),
            ('partner_id', '=', self.partner_id.id),
            ('account_id', 'in', self.account_ids.ids)
        ]
        if not self.show_draft:
            opening_domain.append(('move_id.state', '=', 'posted'))
        
        move_lines = self.env['account.move.line'].search(opening_domain)
        return sum(line.debit - line.credit for line in move_lines)
    
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
        current_year = datetime.date.today().strftime("%Y")
        current_month = datetime.date.today().strftime("%B")
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
            
            
    # def print_partner_ledger(self):
    #     """ Trigger the report action for the Partner Ledger """
    #     #data = self.load_data()
    #     #print("==================data==================================",data)
    #
    #     return self.env.ref('zb_financial_reports.partner_ledger_reportss').report_action(self, data={})
    #
    #

    # def load_data(self):
    #     analytic_fields = self.env['ir.model.fields'].search([('model_id.model', '=', 'account.analytic.line'), ('relation', '=', 'account.analytic.account')])
    #     print("Analytic fields:", analytic_fields)
    #
    #     for rec in self:
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
    #             account_type_map = {
    #                 'asset_receivable': ['asset_receivable'],
    #                 'liability_payable': ['liability_payable'],
    #                 'receivable_payable': ['asset_receivable', 'liability_payable']
    #             }
    #             domain.append(('account_type', 'in', account_type_map.get(rec.account_type, ['asset_receivable', 'liability_payable'])))
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
    #         # Prepare a list of dictionaries for QWeb report
    #         line_list = []
    #
    #         if rec.group_by == 'partner':
    #             print("Grouping by partner")
    #             partner_ids = set(line_ids.mapped('partner_id'))
    #             for partner in partner_ids:
    #                 opening_balance = sum(self.env['account.move.line'].search([('partner_id', '=', partner.id), ('date', '<', rec.from_date), ('parent_state', '=', 'posted'), ('account_type', 'in', ['asset_receivable', 'liability_payable'])]).mapped('debit')) \
    #                                 - sum(self.env['account.move.line'].search([('partner_id', '=', partner.id), ('date', '<', rec.from_date), ('parent_state', '=', 'posted')]).mapped('credit'))
    #
    #                 opening_balance_currency = sum(self.env['account.move.line'].search([('partner_id', '=', partner.id), ('date', '<', rec.from_date), ('parent_state', '=', 'posted')]).mapped('amount_currency'))
    #
    #                 print(f"Opening balances for partner {partner.display_name}: Balance={opening_balance}, Currency Balance={opening_balance_currency}")
    #
    #                 opening_entry = {
    #                     'name': partner.display_name,
    #                     'ref': 'Opening Balance',
    #                     'balance': opening_balance,
    #                     'balance_currency': opening_balance_currency,
    #                 }
    #                 line_list.append(opening_entry)
    #
    #                 # Lines grouped by partner
    #                 for line in line_ids.filtered(lambda l: l.partner_id == partner):
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
    #                         'balance': opening_balance + (line.debit - line.credit),
    #                         'balance_currency': opening_balance_currency + line.amount_currency,
    #                     }
    #                     print("Appending line values:", vals)
    #                     line_list.append(vals)
    #                     opening_balance += (line.debit - line.credit)
    #                     opening_balance_currency += line.amount_currency
    #         else:
    #             for line in line_ids:
    #                 vals = {
    #                     'date': line.date,
    #                     'ref': f"{line.move_id.name}-{line.move_id.ref}[{line.date.strftime('%d/%m/%y')}]",
    #                     'label': line.name,
    #                     'account_id': line.account_id.id,
    #                     'partner_id': line.partner_id.id,
    #                     'analytic_account_id': line.analytic_account_id.id,
    #                     'amount_currency': line.amount_currency,
    #                     'currency_id': line.currency_id.id,
    #                     'move_line_id': line.id,
    #                     'debit': line.debit,
    #                     'credit': line.credit,
    #                     'balance': line.debit - line.credit,
    #                     'balance_currency': line.amount_currency,
    #                 }
    #                 print("Appending line values in else block:", vals)
    #                 line_list.append(vals)
    #
    #         print("Final line list for QWeb report:", line_list)
    #
    #         return line_list
    