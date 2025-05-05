from odoo import models
import datetime

class TrialBalanceXlsx(models.AbstractModel):
    _name = 'report.zb_financial_reports.trial_balance_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description="Ins Trial Balance Report"

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
    #                       'heading_format_4': workbook.add_format({'align': 'left',
    #                                                                'valign': 'vjustify',
    #                                                                'bold': True, 'size': 11,
    #                                                                'font_name': 'Times New Roman',
    #                                                                # 'bg_color': 'FFFFCC',
    #                                                                'color': 'black',
    #                                                                'border': True,
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
    #     worksheet.merge_range('D1:F1', company_name, design_formats['heading_format_2'])
    #     worksheet.merge_range('D2:F2', 'Trial Balance', design_formats['heading_format_2'])
    #
    #     worksheet.write(4, 0, 'From Date : ', design_formats['heading_format_1'])
    #     worksheet.write(4, 1, obj.from_date if obj.from_date else '', design_formats['date_format'])
    #     worksheet.write(5, 0, 'To Date : ', design_formats['heading_format_1'])
    #     worksheet.write(5, 1, obj.to_date if obj.to_date else '', design_formats['date_format'])
    #
    #     worksheet.write(6, 0, 'Display Type : ', design_formats['heading_format_1'])
    #     display_type = ''
    #     if obj.display_type == 'balance_only':
    #         display_type = 'Balance Only'
    #     elif obj.display_type == 'complete':
    #         display_type = 'Complete'
    #
    #
    #     worksheet.write(6, 1, display_type, design_formats['normal_format_central'])
    #     #
    #     # worksheet.write(4, 2, 'Partner(s) : ', design_formats['heading_format_1'])
    #     # partner_name = ''
    #     # if obj.partner_ids:
    #     #     for partner in obj.partner_ids:
    #     #         partner_name += partner.name + ','
    #     # worksheet.write(4, 3, partner_name, design_formats['normal_format_central'])
    #     # worksheet.write(5, 2, 'Analytic Account : ', design_formats['heading_format_1'])
    #     # worksheet.write(5, 3, obj.analytic_account_id.name if obj.analytic_account_id else '', design_formats['heading_format_1'])
    #     # worksheet.write(6, 2, 'Label : ', design_formats['heading_format_1'])
    #     # worksheet.write(6, 3, obj.label if obj.label else '', design_formats['heading_format_1'])
    #
    #     if obj.display_type == 'balance_only':
    #         worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
    #         worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
    #         worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
    #
    #         worksheet.write(8, 3, 'Opening', design_formats['heading_format_3'])
    #
    #         worksheet.write(9, 3, 'Balance', design_formats['heading_format_3'])
    #         worksheet.merge_range('E9:F9', 'Transactions', design_formats['heading_format_3'])
    #         worksheet.write(9, 4, 'Debit', design_formats['heading_format_3'])
    #         worksheet.write(9, 5, 'Credit', design_formats['heading_format_3'])
    #
    #         worksheet.write(8, 6, 'Closing', design_formats['heading_format_3'])
    #         worksheet.write(9, 6, 'Balance', design_formats['heading_format_3'])
    #         row = 9
    #         col = 0
    #
    #         total_debit = 0.0
    #         total_credit = 0.0
    #         total_opening_balance = 0.0
    #         total_closing_balance = 0.0
    #
    #         for line in obj.trial_balance_line_ids:
    #             type_label = dict(line._fields['type'].selection).get(line.type)
    #
    #             row += 1
    #             worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
    #             worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
    #             worksheet.write(row, col + 3, line.opening_balance if line.opening_balance else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 4,line.debit if line.debit else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 5,line.credit if line.credit else '',design_formats['normal_format_right'])
    #             worksheet.write(row, col + 6,line.closing_balance if line.closing_balance else '',design_formats['normal_format_right'])
    #
    #             total_debit += line.debit
    #             total_credit += line.credit
    #             total_opening_balance += line.opening_balance
    #             total_closing_balance += line.closing_balance
    #
    #         worksheet.write(row+2, col + 3, round(total_opening_balance,2), design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 4,total_debit, design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 5,total_credit,design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 6, round(total_closing_balance,2), design_formats['normal_format_right'])
    #
    #
    #     elif obj.display_type == 'complete':
    #         worksheet.merge_range('D9:F9', 'Opening', design_formats['heading_format_3'])
    #         worksheet.merge_range('G9:I9', 'Opening', design_formats['heading_format_3'])
    #         worksheet.merge_range('J9:L9', 'Opening', design_formats['heading_format_3'])
    #
    #
    #         worksheet.write(9, 0, 'Code', design_formats['heading_format_3'])
    #         worksheet.write(9, 1, 'Name', design_formats['heading_format_4'])
    #         worksheet.write(9, 2, 'Type', design_formats['heading_format_4'])
    #         worksheet.write(9, 3, 'Debit', design_formats['heading_format_3'])
    #         worksheet.write(9, 4, 'Credit', design_formats['heading_format_3'])
    #         worksheet.write(9, 5, 'Balance', design_formats['heading_format_3'])
    #         worksheet.write(9, 6, 'Debit', design_formats['heading_format_3'])
    #         worksheet.write(9, 7, 'Credit', design_formats['heading_format_3'])
    #         worksheet.write(9, 8, 'Balance', design_formats['heading_format_3'])
    #         worksheet.write(9, 9, 'Debit', design_formats['heading_format_3'])
    #         worksheet.write(9, 10, 'Credit', design_formats['heading_format_3'])
    #         worksheet.write(9, 11, 'Balance', design_formats['heading_format_3'])
    #         row = 9
    #         col = 0
    #
    #         total_debit1 = 0
    #         total_debit2 = 0
    #         total_debit3 = 0
    #
    #
    #         total_credit1 = 0
    #         total_credit2 = 0
    #         total_credit3 = 0
    #
    #         total_opening_balance1 = 0
    #         total_opening_balance2 = 0
    #         total_opening_balance3 = 0
    #
    #         for line in obj.trial_balance_complete_line_ids:
    #             type_label = dict(line._fields['type'].selection).get(line.type)
    #             row += 1
    #             worksheet.write(row, col, line.code if line.code else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 1, line.name if line.name else '', design_formats['normal_format_left'])
    #             worksheet.write(row, col + 2, type_label if line.type else '', design_formats['normal_format_left'])
    #             worksheet.write(row, col + 3, line.debit1 if line.debit1 else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 4,line.credit1 if line.credit1 else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 5,line.opening_balance1 if line.opening_balance1 else '',design_formats['normal_format_right'])
    #             worksheet.write(row, col + 6, line.debit2 if line.debit2 else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 7,line.credit2 if line.credit2 else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 8,line.opening_balance2 if line.opening_balance2 else '',design_formats['normal_format_right'])
    #             worksheet.write(row, col + 9, line.debit3 if line.debit3 else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 10,line.credit3 if line.credit3 else '', design_formats['normal_format_right'])
    #             worksheet.write(row, col + 11,line.opening_balance3 if line.opening_balance3 else '',design_formats['normal_format_right'])
    #
    #             total_debit1 += line.debit1
    #             total_debit2 += line.debit2
    #             total_debit3 += line.debit3
    #
    #
    #             total_credit1 += line.credit1
    #             total_credit2 += line.credit2
    #             total_credit3 += line.credit3
    #
    #             total_opening_balance1 += line.opening_balance1
    #             total_opening_balance2 += line.opening_balance2
    #             total_opening_balance3 += line.opening_balance3
    #
    #         worksheet.write(row+2, col + 3, total_debit1, design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 4,total_credit1, design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 5,round(total_opening_balance1,2),design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 6, total_debit2, design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 7,total_credit2, design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 8,round(total_opening_balance2,2),design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 9, total_debit3, design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 10,total_credit3, design_formats['normal_format_right'])
    #         worksheet.write(row+2, col + 11,round(total_opening_balance3,2),design_formats['normal_format_right'])
