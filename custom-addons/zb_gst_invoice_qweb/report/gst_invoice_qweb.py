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

from odoo import models, api


class GSTInvoiceQwebReport(models.AbstractModel):
    _name = 'report.zb_gst_invoice_qweb.report_gst_invoice_qweb'
    _description = 'GST Invoice Report'

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     docs = self.env['account.move'].browse(data['context'].get('active_id', False))
    #     return {
    #         'doc_ids': docids,
    #         'doc_model': 'account.move',
    #         'docs': docs,
    #         'data': data,
    #         'doc_types': data.get('doc_types', [])
    #     }
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docids = docids or data.get('context', {}).get('active_ids', [])
        docs = self.env['account.move'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'data': data,
            'doc_types': data.get('doc_types', [])
        }
