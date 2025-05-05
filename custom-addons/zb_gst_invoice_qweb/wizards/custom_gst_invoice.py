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

from odoo import fields, models, api


class CustomGstInvoice(models.TransientModel):
    _name = 'custom.gst.invoice'
    _description = 'Custom GST Invoice'

    original_copy = fields.Boolean("Original Copy", default=True)
    duplicate_copy = fields.Boolean("Duplicate Copy", default=True)
    triplicate_copy = fields.Boolean("Triplicate Copy", default=True)
    extra_copy = fields.Boolean("Extra Copy")

    def action_print(self):
        report = self.env.ref('zb_gst_invoice_qweb.gst_invoice_report_qweb_template')
        doc_ids = self.env[self._context['active_model']].browse(self._context.get('active_ids', [])).ids
        doc_types = []
        if self.original_copy:
            doc_types.append("original_copy")
        if self.duplicate_copy:
            doc_types.append("duplicate_copy")
        if self.triplicate_copy:
            doc_types.append("triplicate_copy")
        if self.extra_copy:
            doc_types.append("extra_copy")
        action = report.report_action(doc_ids, data={'doc_types': doc_types})
        return action

