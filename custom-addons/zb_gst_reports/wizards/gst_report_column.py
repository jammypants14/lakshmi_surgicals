#  -*- encoding: utf-8 -*-
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

from odoo import models


class GstReportColumn(models.TransientModel):
    _name = "gst.report.column"
    _description = "CSV column"

    def get_b2b_column(self, gstType):
        columns = []
        if gstType == 'gstr1':
            columns = [
                'GSTIN/UIN of Recipient',
                'Receiver Name',
                'Invoice Number',
                'Invoice date',
                'Invoice Value',
                'Place Of Supply',
                'Reverse Charge',
                'Applicable % of Tax Rate',
                'Invoice Type',
                'E-Commerce GSTIN',
                'Rate',
                'Taxable Value',
                'Cess Amount'
            ]
        if gstType == 'gstr2':
            columns = [
                'GSTIN of Supplier',
                'Invoice Number',
                'Invoice date',
                'Invoice Value',
                'Place Of Supply',
                'Reverse Charge',
                'Invoice Type',
                'Rate',
                'Taxable Value',
                'Integrated Tax Paid',
                'Central Tax Paid',
                'State/UT Tax Paid',
                'Cess Amount',
                'Eligibility For ITC',
                'Availed ITC Integrated Tax',
                'Availed ITC Central Tax',
                'Availed ITC State/UT Tax',
                'Availed ITC Cess'
            ]

        return columns

    def get_b2b_nil_column(self):
        return ["", "Taxable Value"]

    def get_b2cs_column(self):
        columns = [
            'Type',
            'Place Of Supply',
            'Applicable % of Tax Rate',
            'Rate',
            'Taxable Value',
            'Cess Amount',
            'E-Commerce GSTIN'
        ]
        return columns

    def get_export_column(self):
        columns = [
            'Export Type',
            'Invoice Number',
            'Invoice date',
            'Invoice Value',
            'Port Code',
            'Shipping Bill Number',
            'Shipping Bill Date',
            'Applicable % of Tax Rate',
            'Rate',
            'Taxable Value'
        ]
        return columns

    def get_cdnr_column(self, gstType):
        columns = []
        if gstType == 'gstr1':
            columns = [
                'GSTIN/UIN of Recipient',
                'Receiver Name',
                'Invoice/Advance Receipt Number',
                'Invoice/Advance Receipt date',
                'Note/Refund Voucher Number',
                'Note/Refund Voucher date',
                'Pre GST',
                'Document Type',
                'Place Of Supply',
                'Note/Refund Voucher Value',
                'Applicable % of Tax Rate',
                'Rate',
                'Taxable Value',
                'Cess Amount'
            ]
        if gstType == 'gstr2':
            columns = [
                'GSTIN of Supplier',
                'Note/Refund Voucher Number',
                'Note/Refund Voucher date',
                'Invoice/Advance Payment Voucher Number',
                'Invoice/Advance Payment Voucher date',
                'Pre GST',
                'Document Type',
                'Reason For Issuing document',
                'Supply Type',
                'Note/Refund Voucher Value',
                'Rate',
                'Taxable Value',
                'Integrated Tax Paid',
                'Central Tax Paid',
                'State/UT Tax Paid',
                'Cess Paid',
                'Eligibility For ITC',
                'Availed ITC Integrated Tax',
                'Availed ITC Central Tax',
                'Availed ITC State/UT Tax',
                'Availed ITC Cess'
            ]
        return columns

    def get_hsn_column(self):
        columns = [
            'HSN',
            'Description',
            'UQC',
            'Total Quantity',
            'Total Value',
            'Rate',
            'Taxable Value',
            'Integrated Tax Amount',
            'Central Tax Amount',
            'State/UT Tax Amount',
            'Cess Amount'
        ]
        return columns
    
    def get_inv_count_column(self):
        columns = [
            'Nature of Document',
            'Sr. No. From',
            'Sr. No. To',
            'Total Number',
            'Posted',
            'Cancelled',
            'jumped',
            'Missing Sr. No.'
            
        ]
        return columns
