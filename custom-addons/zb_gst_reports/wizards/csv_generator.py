#  -*- encoding: utf-8 -*-
#  OpenERP, Open Source Management Solution
#  Copyright (C) 2016 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>)
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
import base64
import csv
import io

from odoo import fields, models


class CsvGenerator(models.TransientModel):
    _name = 'csv.generator'
    _description = 'CSV Generator'

    def generate_all_csvs(self):
        report = self.env['gst.reports'].browse(self._context.get('report_id', False))
        if report:
            csv_data = report.get_csv_data()
            if csv_data.get('b2b', False):
                title_row = self.env['gst.report.column'].get_b2b_column(report.report_type)
                file_name = report.report_type + "_B2B_" + str(fields.Date.today()) + '.csv'
                attachment_id = self.generate_csv(csv_data['b2b'], title_row, file_name, report.id)
                report.b2b_attachment_id = attachment_id
            if csv_data.get('b2b_nil', False):
                title_row = self.env['gst.report.column'].get_b2b_nil_column()
                file_name = report.report_type + "_B2B_NIL_" + str(fields.Date.today()) + '.csv'
                self_obj = self.with_context({'b2b_nil': True})
                attachment_id = self_obj.generate_csv(csv_data['b2b_nil'], title_row, file_name, report.id)
                report.b2b_nil_attachment_id = attachment_id
            if csv_data.get('b2cs', False):
                title_row = self.env['gst.report.column'].get_b2cs_column()
                file_name = report.report_type + "_B2CS_" + str(fields.Date.today()) + '.csv'
                attachment_id = self.generate_csv(csv_data['b2cs'], title_row, file_name, report.id)
                report.b2cs_attachment_id = attachment_id
            if csv_data.get('hsn', False):
                title_row = self.env['gst.report.column'].get_hsn_column()
                file_name = report.report_type + "_HSN_" + str(fields.Date.today()) + '.csv'
                attachment_id = self.generate_csv(csv_data['hsn'], title_row, file_name, report.id)
                report.hsn_attachment_id = attachment_id
            if csv_data.get('cdnr', False):
                title_row = self.env['gst.report.column'].get_cdnr_column(report.report_type)
                file_name = report.report_type + "_CDNR_" + str(fields.Date.today()) + '.csv'
                attachment_id = self.generate_csv(csv_data['cdnr'], title_row, file_name, report.id)
                report.cdnr_attachment_id = attachment_id
            if csv_data.get('export', False):
                title_row = self.env['gst.report.column'].get_export_column()
                file_name = report.report_type + "_EXPORT_" + str(fields.Date.today()) + '.csv'
                attachment_id = self.generate_csv(csv_data['export'], title_row, file_name, report.id)
                report.export_attachment_id = attachment_id
            if csv_data.get('inv_count_dict', False):
                title_row = self.env['gst.report.column'].get_inv_count_column()
                file_name = report.report_type + "_INV COUNT_" + str(fields.Date.today()) + '.csv'
                attachment_id = self.generate_csv(csv_data['inv_count_dict'], title_row, file_name, report.id)
                report.invoice_count_attachment_id = attachment_id

    def generate_csv(self, rows, title_row, file_name, report_id):
        fp = io.StringIO()
        writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL, escapechar='\\')
        writer.writerow(title_row)
        if self._context.get('b2b_nil', False):
            writer.writerow(["Intra-state supplies to registered persons", rows['intra_state_registered']])
            writer.writerow(["Intra-state supplies to unregistered persons", rows['intra_state_unregistered']])
            writer.writerow(["Inter-state supplies to registered persons", rows['inter_state_registered']])
            writer.writerow(["Inter-state supplies to unregistered persons", rows['inter_state_unregistered']])
        else:
            for row in rows:
                writer.writerow(row)
        fp.seek(0)
        data = fp.read()
        fp.close()
        attachment = self.env['ir.attachment'].create({
            'datas': base64.b64encode(data.encode('utf-8')),
            'type': 'binary',
            'res_model': 'gst.reports',
            'res_id': report_id,
            'db_datas': file_name,
            'store_fname': file_name,
            'name': file_name
        })
        return attachment.id
