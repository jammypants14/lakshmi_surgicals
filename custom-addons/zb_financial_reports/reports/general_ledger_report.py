from odoo import models
import datetime

class GeneralLedgerXlsx(models.AbstractModel):
    _name = 'report.zb_financial_reports.general_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description="Ins General Report"

    # def generate_xlsx_report(self, workbook, data, ledger):
    #     for obj in ledger:
    #         report_name = obj.name
    #         # One sheet by partner
    #         worksheet = workbook.add_worksheet(report_name[:31])
    #         # bold = workbook.add_format({'bold': True})
    #         # sheet.write(0, 0, obj.name, bold)
    #
    #
    #         design_formats = {'heading_format': workbook.add_format({'align': 'center',
    #                                                              'valign': 'vcenter',
    #                                                              'bold': True, 'size': 25,
    #                                                              'font_name': 'Times New Roman',
    #                                                              'text_wrap': True,
    #                                                              # 'bg_color': 'blue', 'color' : 'white',
    #                                                              'text_wrap': True, 'shrink': True}),
    #                       'heading_format_1': workbook.add_format({'align': 'left',
    #                                                                'valign': 'vjustify',
    #                                                                'bold': True, 'size': 11,
    #                                                                'font_name': 'Times New Roman',
    #                                                                # 'bg_color': 'FFFFCC',
    #                                                                # 'color': 'black',
    #                                                                'border': False,
    #                                                                'text_wrap': True, 'shrink': True}),
    #                       'heading_format_3': workbook.add_format({'align': 'center',
    #                                                                'valign': 'vjustify',
    #                                                                'bold': True, 'size': 11,
    #                                                                'font_name': 'Times New Roman',
    #                                                                # 'bg_color': 'FFFFCC',
    #                                                                'color': 'black',
    #                                                                'border': True,
    #                                                                'text_wrap': True, 'shrink': True}),
    #                       'heading_format_2': workbook.add_format({'align': 'center',
    #                                                                'valign': 'vjustify',
    #                                                                'bold': True, 'size': 12,
    #                                                                'font_name': 'Times New Roman',
    #                                                                'color': 'black',
    #                                                                'border': False,
    #                                                                'text_wrap': True, 'shrink': True}),
    #                       'merged_format': workbook.add_format({'align': 'center',
    #                                                             'valign': 'vjustify',
    #                                                             'bold': True, 'size': 17,
    #                                                             'font_name': 'Times New Roman',
    #                                                             # 'bg_color': 'blue', 'color' : 'white',
    #                                                             'text_wrap': True, 'shrink': True}),
    #                       'sub_heading_format': workbook.add_format({'align': 'right',
    #                                                                  'valign': 'vjustify',
    #                                                                  'bold': True, 'size': 11,
    #                                                                  'font_name': 'Times New Roman',
    #                                                                  # 'bg_color': 'yellow', 'color' : 'black',
    #                                                                  'text_wrap': True, 'shrink': True}),
    #                       'sub_heading_format_left': workbook.add_format({'align': 'left',
    #                                                                       'valign': 'vjustify',
    #                                                                       'bold': False, 'size': 9,
    #                                                                       'font_name': 'Times New Roman',
    #                                                                       # 'bg_color': 'yellow', 'color' : 'black',
    #                                                                       'text_wrap': True, 'shrink': True}),
    #                       'sub_heading_format_center': workbook.add_format({'align': 'center',
    #                                                                         'valign': 'vjustify',
    #                                                                         'bold': True, 'size': 9,
    #                                                                         'font_name': 'Times New Roman',
    #                                                                         # 'bg_color': 'yellow', 'color' : 'black',
    #                                                                         'text_wrap': True, 'shrink': True}),
    #                       'bold': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
    #                                                    'size': 11,
    #                                                    'text_wrap': True}),
    #                       'bold_center': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
    #                                                           'size': 11,
    #                                                           'text_wrap': True,
    #                                                           'align': 'center',
    #                                                           'border': True, }),
    #                       'bold_border': workbook.add_format({'bold': True, 'font_name': 'Times New Roman',
    #                                                           'size': 11, 'text_wrap': True,
    #                                                           'border': True, }),
    #                       'date_format_border': workbook.add_format({'num_format': 'dd/mm/yyyy',
    #                                                           'font_name': 'Times New Roman', 'size': 11,
    #                                                           'align': 'center', 'text_wrap': True,
    #                                                           'border': True, }),
    #                       'date_format': workbook.add_format({'num_format': 'dd/mm/yyyy',
    #                                                           'font_name': 'Times New Roman', 'size': 11,
    #                                                           'align': 'center', 'text_wrap': True,
    #                                                           }),
    #                       'datetime_format': workbook.add_format({'num_format': 'dd/mm/yyyy hh:mm:ss',
    #                                                               'font_name': 'Times New Roman', 'size': 11,
    #                                                               'align': 'center', 'text_wrap': True}),
    #                       'normal_format': workbook.add_format({'font_name': 'Times New Roman',
    #                                                             'size': 11, 'text_wrap': True, 'italic': True, 'bold': True, }),
    #                       'normal_format_right': workbook.add_format({'font_name': 'Times New Roman',
    #                                                                   'align': 'right', 'size': 11,
    #                                                                   'text_wrap': True}),
    #                       'normal_format_left': workbook.add_format({'font_name': 'Times New Roman',
    #                                                                   'align': 'left', 'size': 11,
    #                                                                   'text_wrap': True}),
    #                       'normal_format_central': workbook.add_format({'font_name': 'Times New Roman',
    #                                                                     'size': 11, 'align': 'center',
    #                                                                     'text_wrap': True,
    #                                                                     }),
    #                       'normal_format_central_border': workbook.add_format({'font_name': 'Times New Roman',
    #                                                                     'size': 11, 'align': 'center',
    #                                                                     'text_wrap': True,
    #                                                                     'border': True, }),
    #                       'amount_format': workbook.add_format({'num_format': '#,##0.00',
    #                                                             'font_name': 'Times New Roman',
    #                                                             'align': 'right', 'size': 11,
    #                                                             'text_wrap': True,
    #                                                             'border': True, }),
    #                       'amount_format_2': workbook.add_format({'num_format': '#,##0.00',
    #                                                               'font_name': 'Times New Roman',
    #                                                               'bold': True,
    #                                                               'align': 'right', 'size': 11,
    #                                                               'text_wrap': True,
    #                                                               'border': True, }),
    #                       'amount_format_1': workbook.add_format({'num_format': '#,##0',
    #                                                               'font_name': 'Times New Roman',
    #                                                               'align': 'right', 'size': 11,
    #                                                               'text_wrap': True}),
    #                       'normal_num_bold': workbook.add_format({'bold': True, 'num_format': '#,##0.00',
    #                                                               'font_name': 'Times New Roman',
    #                                                               'align': 'right', 'size': 11,
    #                                                               'text_wrap': True}),
    #                       'float_format': workbook.add_format({'num_format': '###0.00',
    #                                                                 'font_name': 'Times New Roman',
    #                                                                 'align': 'center', 'size': 11,
    #                                                                 'text_wrap': True,
    #                                                                 'border': False, }),
    #                       'int_rate_format': workbook.add_format({'num_format': '###0',
    #                                                               'font_name': 'Times New Roman',
    #                                                               'align': 'right', 'size': 11,
    #                                                               'text_wrap': True}),
    #                                                               }
    #
    #     worksheet.set_column('A:A', 30)
    #     worksheet.set_column('B:B', 30)
    #     worksheet.set_column('C:C', 25)
    #     worksheet.set_column('D:D', 30)
    #     worksheet.set_column('E:E', 30)
    #     worksheet.set_column('F:F', 30)
    #     worksheet.set_column('G:G', 20)
    #     worksheet.set_column('H:H', 20)
    #     worksheet.set_column('I:I', 20)
    #     worksheet.set_column('J:J', 20)
    #     worksheet.set_column('K:K', 20)
    #     worksheet.set_column('L:L', 20)
    #     worksheet.set_column('M:M', 20)
    #     worksheet.set_column('N:N', 20)
    #     worksheet.set_column('O:O', 20)
    #     worksheet.set_column('P:P', 20)
    #     worksheet.set_column('Q:Q', 30)
    #     worksheet.set_column('R:R', 20)
    #     worksheet.set_column('S:S', 20)
    #     worksheet.set_column('T:T', 20)
    #     worksheet.set_column('U:U', 20)
    #     worksheet.set_column('V:V', 20)
    #     worksheet.set_column('W:W', 20)
    #     worksheet.set_column('X:X', 20)
    #     worksheet.set_column('Y:Y', 20)
    #     worksheet.set_column('Z:Z', 20)
    #     worksheet.set_column('AA:AA',20)
    #
    #     current_year = datetime.date.today().strftime("%Y")
    #     current_month = datetime.date.today().strftime("%B")
    #     company_name = self.env.company.name
    #     worksheet.merge_range('F1:H1', company_name, design_formats['heading_format_2'])
    #     worksheet.merge_range('F2:H2', 'General Ledger', design_formats['heading_format_2'])
    #     worksheet.merge_range('F2:H2', 'General Ledger', design_formats['heading_format_2'])
    #
    #     worksheet.write(4, 0, 'From Date : ', design_formats['heading_format_1'])
    #     worksheet.write(4, 1, obj.from_date if obj.from_date else '', design_formats['date_format'])
    #     worksheet.write(5, 0, 'To Date : ', design_formats['heading_format_1'])
    #     worksheet.write(5, 1, obj.to_date if obj.to_date else '', design_formats['date_format'])
    #
    #     worksheet.write(6, 0, 'Account(s) : ', design_formats['heading_format_1'])
    #     account_name = ''
    #     if obj.account_ids:
    #         for account in obj.account_ids:
    #             account_name += account.display_name + ','
    #     worksheet.write(6, 1, account_name, design_formats['normal_format_central'])
    #
    #     worksheet.write(4, 2, 'Partner(s) : ', design_formats['heading_format_1'])
    #     partner_name = ''
    #     if obj.partner_ids:
    #         for partner in obj.partner_ids:
    #             partner_name += partner.name + ','
    #     worksheet.write(4, 3, partner_name, design_formats['normal_format_central'])
    #     worksheet.write(5, 2, 'Analytic Account : ', design_formats['heading_format_1'])
    #     worksheet.write(5, 3, obj.analytic_account_id.name if obj.analytic_account_id else '', design_formats['heading_format_1'])
    #     worksheet.write(6, 2, 'Label : ', design_formats['heading_format_1'])
    #     worksheet.write(6, 3, obj.label if obj.label else '', design_formats['heading_format_1'])
    #
    #
    #     worksheet.write(9, 0, 'Name', design_formats['heading_format_3'])
    #     worksheet.write(9, 1, 'Date', design_formats['heading_format_3'])
    #     worksheet.write(9, 2, 'Reference', design_formats['heading_format_3'])
    #     worksheet.write(9, 3, 'Label', design_formats['heading_format_3'])
    #     worksheet.write(9, 4, 'Account', design_formats['heading_format_3'])
    #     worksheet.write(9, 5, 'Partner', design_formats['heading_format_3'])
    #     worksheet.write(9, 6, 'Analytic Account', design_formats['heading_format_3'])
    #     if obj.is_foreign_currency:
    #         worksheet.write(9, 7, 'Amount Currency', design_formats['heading_format_3'])
    #         worksheet.write(9, 8, 'Currency', design_formats['heading_format_3'])
    #         worksheet.write(9, 9, 'Debit', design_formats['heading_format_3'])
    #         worksheet.write(9, 10, 'Credit', design_formats['heading_format_3'])
    #         worksheet.write(9, 11, 'Balance', design_formats['heading_format_3'])
    #         worksheet.write(9, 12, 'Balance Currency', design_formats['heading_format_3'])
    #     else:
    #         worksheet.write(9, 7, 'Debit', design_formats['heading_format_3'])
    #         worksheet.write(9, 8, 'Credit', design_formats['heading_format_3'])
    #         worksheet.write(9, 9, 'Balance', design_formats['heading_format_3'])
    #
    #     row = 9
    #     col = 0
    #
    #     for line in obj.general_ledger_line_ids:
    #         row += 1
    #         worksheet.write(row, col, line.name if line.name else '', design_formats['normal_format_left'])
    #         worksheet.write(row, col + 1, line.date if line.date else '', design_formats['date_format'])
    #         worksheet.write(row, col + 2, line.ref if line.ref else '', design_formats['normal_format_central'])
    #         worksheet.write(row, col + 3, line.label if line.label else '', design_formats['normal_format_central'])
    #         worksheet.write(row, col + 4,line.counter_account if line.counter_account else '', design_formats['normal_format_central'])
    #         worksheet.write(row, col + 5,line.partner_id.name if line.partner_id else '',design_formats['normal_format_central'])
    #         worksheet.write(row, col + 6,line.analytic_account_id.name if line.analytic_account_id else '',design_formats['normal_format_central'])
    #         if obj.is_foreign_currency:
    #             worksheet.write(row, col + 7,line.amount_currency if line.amount_currency else '',design_formats['normal_format_right'])
    #             worksheet.write(row, col + 8,line.currency_id.name if line.currency_id else '',design_formats['normal_format_central'])
    #             worksheet.write(row, col + 9,line.debit,design_formats['normal_format_right'])
    #             worksheet.write(row, col + 10,line.credit,design_formats['normal_format_right'])
    #             worksheet.write(row, col + 11,line.balance,design_formats['normal_format_right'])
    #             worksheet.write(row, col + 12,line.balance_currency,design_formats['normal_format_right'])
    #         else:
    #             worksheet.write(row, col + 7,line.debit,design_formats['normal_format_right'])
    #             worksheet.write(row, col + 8,line.credit,design_formats['normal_format_right'])
    #             worksheet.write(row, col + 9,line.balance,design_formats['normal_format_right'])
    #

