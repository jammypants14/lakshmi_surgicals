from odoo import models
import datetime
from datetime import datetime, timedelta
from collections import defaultdict

class DayBookXlsx(models.AbstractModel):
    _name = 'report.zb_financial_reports.day_book_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description="Ins Day Book Report"

    # def generate_xlsx_report(self, workbook, data, ledger):
    #     for obj in ledger:
    #         report_name = obj.name
    #         worksheet = workbook.add_worksheet(report_name[:31])
    #         design_formats = {'heading_format': workbook.add_format({'align': 'center',
    #                                                              'valign': 'vcenter',
    #                                                              'bold': True, 'size': 18,
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
    #                                                                'bg_color': '#FFFF00',
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
    #                                                                 'align': 'right', 'size': 11,
    #                                                                 'text_wrap': True,
    #                                                                 'border': False, }),
    #                       'float_bold_format': workbook.add_format({'num_format': '###0.00',
    #                                                                 'font_name': 'Times New Roman',
    #                                                                 'align': 'right', 'size': 11,
    #                                                                 'text_wrap': True,
    #                                                                 'bold': True,
    #                                                                 'border': False, }),
    #                       'float_bold_colour_format': workbook.add_format({'num_format': '###0.00',
    #                                                                 'font_name': 'Times New Roman',
    #                                                                 'align': 'right', 'size': 11,
    #                                                                 'text_wrap': True,
    #                                                                 'bold': True,
    #                                                                 'bg_color': '#FFFF00',
    #                                                                 'border': False, }),
    #                       'int_rate_format': workbook.add_format({'num_format': '###0',
    #                                                               'font_name': 'Times New Roman',
    #                                                               'align': 'right', 'size': 11,
    #                                                               'text_wrap': True}),
    #
    #                      'coloured_text_left': workbook.add_format({'align': 'left',
    #                                                                'valign': 'vjustify',
    #                                                                'bold': True, 'size': 11,
    #                                                                'font_name': 'Times New Roman',
    #                                                                'color': 'black',
    #                                                                'border': False,
    #                                                                'bg_color': '#FFFF00',
    #                                                                'text_wrap': True, 'shrink': True}),
    #
    #                                                                 }
    #     worksheet.set_column('A:A', 1)
    #     worksheet.set_column('B:B', 9)
    #     worksheet.set_column('C:C', 50)
    #     worksheet.set_column('D:D', 15)
    #     worksheet.set_column('E:E', 9)
    #     worksheet.set_column('F:F', 50)
    #     worksheet.set_column('G:G', 15)
    #     # current_year = datetime.date.today().strftime("%Y")
    #     # current_month = datetime.date.today().strftime("%B")
    #     company_name = self.env.company.name
    #     worksheet.merge_range('A1:G1', 'DAY BOOK', design_formats['heading_format'])
    #     worksheet.write(2, 1, 'sl#', design_formats['heading_format_1'])
    #     worksheet.write(2, 2, 'Reciept', design_formats['heading_format_1'])
    #     worksheet.write(2, 3, 'amount', design_formats['heading_format_1'])
    #     worksheet.write(2, 4, 'sl#', design_formats['heading_format_1'])
    #     worksheet.write(2, 5, 'Payment', design_formats['heading_format_1'])
    #     worksheet.write(2, 6, 'Payment Value', design_formats['heading_format_1'])
    #     credit_list=[]
    #     debit_list=[]
    #     rows = row = 3
    #     col = 1
    #     credit_total = debit_total = 0
    #     last_closing = total_opening = last_debit = last_credit = 0
    #     for line in obj.day_book_line_ids:
    #         if line.name:
    #
    #             if debit_total:
    #                 worksheet.write(row+2, col+1, '*** TOTAL ***', design_formats['heading_format_1'])
    #                 worksheet.write(row+2, col+2, debit_total, design_formats['float_bold_format'])
    #                 last_debit = last_debit + debit_total
    #
    #                 row += 5
    #             if credit_total:
    #                 worksheet.write(rows+2, col+4, '*** TOTAL ***', design_formats['heading_format_1'])
    #                 worksheet.write(rows+2, col+5, credit_total, design_formats['float_bold_format'])
    #                 last_credit = last_credit + credit_total
    #             closing = debit_total - credit_total
    #             if closing:
    #                 worksheet.write(rows+4, col+4, 'Closing Balance', design_formats['heading_format_1'])
    #                 worksheet.write(rows+4, col+5, closing, design_formats['float_bold_format'])
    #                 rows += 5
    #                 last_closing = last_closing + closing
    #
    #             credit_total = debit_total = 0
    #             i=0
    #             j=0
    #             i+=1
    #             print(rows,row)
    #             if row < rows:
    #                 row=rows
    #             worksheet.merge_range(row, col,row, col+5, line.name if line.name else '', design_formats['heading_format_2'])
    #             worksheet.write(row+1, col, i , design_formats['normal_format_right'])
    #             worksheet.write(row+1, col+1, line.ref if line.ref else '', design_formats['normal_format_left'])
    #             worksheet.write(row+1, col+2, line.balance if line.balance else '', design_formats['float_format'])
    #             debit_total = debit_total + line.balance
    #             rows = row
    #             row+=1
    #             total_opening += line.balance
    #             print(line.name,row,rows)
    #         else:
    #             if line.debit:
    #                 i+=1
    #                 worksheet.write(row+1, col, i , design_formats['normal_format_right'])
    #                 worksheet.write(row+1, col+1, line.partner_id.name if line.partner_id else (line.label if line.label else (line.ref if line.ref else '')), design_formats['normal_format_left'])
    #                 worksheet.write(row+1, col+2, line.debit if line.debit else '', design_formats['float_format'])
    #                 debit_total = debit_total + line.debit
    #                 row+=1
    #             elif line.credit:
    #                 j+=1
    #                 worksheet.write(rows+1, col+3, j , design_formats['normal_format_right'])
    #                 worksheet.write(rows+1, col+4, line.partner_id.name if line.partner_id else (line.label if line.label else (line.ref if line.ref else '')), design_formats['normal_format_left'])
    #                 worksheet.write(rows+1, col+5, line.credit if line.credit else '', design_formats['float_format'])
    #                 credit_total = credit_total + line.credit
    #                 rows+=1
    #     closing = debit_total - credit_total
    #     if rows > row:
    #         row = rows
    #     if debit_total:
    #         worksheet.write(row+2, col+1, '*** TOTAL ***', design_formats['heading_format_1'])
    #         worksheet.write(row+2, col+2, debit_total, design_formats['float_bold_format'])
    #         last_debit = last_debit + debit_total
    #         # row += 5  
    #     print(row,rows)
    #     if credit_total:
    #         rows +=1
    #         worksheet.write(row+2, col+4, '*** TOTAL ***', design_formats['heading_format_1'])
    #         worksheet.write(row+2, col+5, credit_total, design_formats['float_bold_format'])
    #         last_credit = last_credit + credit_total
    #
    #     if closing:
    #         worksheet.write(rows+4, col+4, 'Closing Balance', design_formats['heading_format_1'])
    #         worksheet.write(rows+4, col+5, closing, design_formats['float_bold_format'])
    #         row += 5
    #
    #         last_closing = last_closing + closing
    #     print(rows,row)
    #     # if row > rows:
    #     #     rows = row
    #     worksheet.merge_range(row+3, 1 ,row+3, col+2, 'Summary', design_formats['heading_format'])
    #     formatted_date = (obj.from_date - timedelta(days=1)).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
    #     text_with_date = f"Closing Balance As On {formatted_date}"
    #     worksheet.write(row + 4, col + 1, text_with_date, design_formats['heading_format_1'])
    #     worksheet.write(row+4, col+2, total_opening, design_formats['float_bold_format'])
    #     formatted_date = (obj.to_date).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
    #     text_with_date = f"Total Receipts As On {formatted_date}"
    #     worksheet.write(row+5, col+1, text_with_date, design_formats['heading_format_1'])
    #     worksheet.write(row+5, col+2, last_debit, design_formats['float_bold_format'])
    #     formatted_date = (obj.to_date).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
    #     text_with_date = f"Total Payments As On {formatted_date}"
    #     worksheet.write(row+6, col+1, text_with_date, design_formats['heading_format_1'])
    #     worksheet.write(row+6, col+2, last_credit, design_formats['float_bold_format'])
    #     formatted_date = (obj.to_date).strftime('%d-%m-%Y')  # Example date format: 'YYYY-MM-DD'
    #     text_with_date = f"Closing Balance As On {formatted_date}"
    #     worksheet.write(row + 7, col + 1, text_with_date, design_formats['coloured_text_left'])
    #     worksheet.write(row+7, col+2, last_closing, design_formats['float_bold_colour_format'])
    #

                    
                    
                    
     