# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2025 ZestyBeanz Technologies(<http://www.zbeanztech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, api, _, fields
from odoo.exceptions import UserError
import qrcode
import base64
from io import BytesIO
import json
import requests
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from collections import OrderedDict
import re
import logging

class AccountMove(models.Model):
    _inherit= 'account.move'
    
    @api.onchange('eway_transporter')
    def onchange_transporter(self):
        
        if self.eway_transporter:
            self.eway_transporter_id = self.eway_transporter.vat

    irn = fields.Text(string="IRN", copy=False)
    ack_no = fields.Char("Ack No", copy=False)
    ack_date = fields.Datetime("Ack Date", copy=False)
    reciepient_gstin = fields.Char("Recipient GSTn", copy=False)
    scaned_qr_code = fields.Text("Scanned QR Code", copy=False)
    ewb_no = fields.Char("EWB No.", copy=False)
    ewb_respnse = fields.Text("EWB Response", copy=False)
    data_response = fields.Text("Data", copy=False)
    
    einvoice_generated = fields.Boolean(string="E-Invoice Generated", copy=False)
    eway_generated = fields.Boolean(string="E-way Generated", copy=False)
    transaction_type = fields.Selection([('1', 'Regular'), ('2', 'Bill To - Ship To'),
                                             ('3', 'Bill From - Dispatch From'), ('4', 'Bill To - Ship To and Bill From - Dispatch From')],string="Transaction Type")
    qr_code = fields.Binary("QR Code",compute='generate_qr_code', attachment=True, store=True,copy=False)#
    eway_supply_type = fields.Selection([('I', 'Inward'),
                                         ('O', 'Outward')],
                                        string='Supply Type', store=True)
    eway_sub_supply_type = fields.Selection([('1', 'Supply'), ('2', 'Import'),
                                             ('3', 'Export'), ('4', 'Job Work'),
                                             ('5', 'For Own Use'), ('6', 'Job work Returns'),
                                             ('7', 'Sales Return'), ('8', 'Others'),
                                             ('9', 'SKD/CKD'), ('10', 'Line Sales'),
                                             ('11', 'Recipient  Not Known'),
                                             ('12', 'Exhibition or Fairs')], string="Sub Supply Type", store=True)
    eway_document_type = fields.Selection([('INV', 'Invoice'),
                                           ('BIL', 'Bill'), ('BOE', 'Bill of Entry'),
                                           ('CHL', 'Challan'), ('CNT', 'Credit Note'),
                                           ('OTH', 'Others')], string="Document Type", store=True)
    eway_distance = fields.Integer(string='Distance (Km)')
    eway_bill_no = fields.Char(string='E-Way Bill No', copy=False)
    eway_bill_date = fields.Char(string="Eway Bill Date", copy=False)
    eway_bill_valid_upto = fields.Char(string="Eway Bill Valid Upto", copy=False)
    eway_sub_supply_desc = fields.Char(string="Sub Supply Desc")
    eway_transporter = fields.Many2one('res.partner', string="Transporter")
    eway_transporter_id = fields.Char(string='Transporter ID')
    eway_transporter_type = fields.Selection([('R', 'Regular')], string="Transporter Type", store=True)
    eway_transport_date = fields.Date(string='Transport Date')
    eway_transport_doc_no = fields.Char(string='Transport Doc#')
    eway_vehicle_no = fields.Char("Vehicle No")
    eway_transportation_mode = fields.Selection([('1', 'Road'),
                                                 ('2', 'Rail'), ('3', 'Air'),
                                                 ('4', 'Ship')], string='Transportation Mode', store=True)

    
 
    @api.model
    def default_get(self, fields):
        rec = super(AccountMove, self).default_get(fields)
        
        inv_type = rec.get('move_type', False)
        print("rec",rec,inv_type)
        if inv_type:
            if inv_type == "out_invoice":
                rec.update({
                    'eway_supply_type': 'O',
                    'eway_document_type': 'INV',
                    'eway_sub_supply_type': '1'
                })
            else:
                rec.update({
                    'eway_supply_type': 'I',
                    'eway_document_type': 'BIL',
                })
        return rec
#
#
#
    @api.depends('scaned_qr_code')
    def generate_qr_code(self):
        for rec in self:
            if rec.scaned_qr_code:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(rec.scaned_qr_code)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.qr_code = qr_image
#
#
    def generate_gst_einvoice_bill(self):

        self = self.with_context({
            'data': self.env.context.get('active_ids', []),
        })

        [form_data] = self.read()
        data = {
            'form': form_data
        }
        return  self.env.ref('zb_gst_einvoice_irn.report_json_einvoice').report_action(self, data=data, config=False)
#
    def generate_gst_ewaybill(self):
        data = {
            'ids': self.env.context.get('active_ids', []),
        }
        self = self.with_context({
            'data': data
        })
        [form_data] = self.read()
        data = {
            'form': form_data
        }

        return  self.env.ref('zb_gst_einvoice_irn.report_json_ewaybill_einvoice').report_action(self, data=data, config=False)
#
#
    def fetch_irn_from_gst_portal(self):

        companyno=0
        journalno=0
        company_info = self.company_id
        journal_info = self.journal_id
        
        if journal_info.api_username and journal_info.api_password and journal_info.ip_address and journal_info.api_client_id and journal_info.api_client_secret and journal_info.api_gstin and journal_info.api_auth_url and journal_info.api_einvoice_url:
            journalno = 1 
    
            headers = {"Content-Type": "application/json",
                       "username":  journal_info.api_username,
                       "password": journal_info.api_password,
                       "ip_address": journal_info.ip_address,
                       "client_id": journal_info.api_client_id,
                       "client_secret": journal_info.api_client_secret,
                       "gstin": journal_info.api_gstin}
    
            url =  journal_info.api_auth_url
    
            json_data = {}
    
            response = requests.get(url, headers=headers)
            response_content = json.loads(response.content)
            if response_content['status_cd']=='Sucess':
                journal_info.update({"auth_token":response_content['data']['AuthToken']})
    
            else:
                raise UserError("E-Invoice not successful authentication")
    
    
            headers = {"Content-Type": "application/json",
                       "username":  journal_info.api_username,
                       "auth-token": journal_info.auth_token,
                       "ip_address": journal_info.ip_address,
                       "client_id": journal_info.api_client_id,
                       "client_secret": journal_info.api_client_secret,
                       "gstin": journal_info.api_gstin}
    
            url =  journal_info.api_einvoice_url
            
        elif company_info.api_username and company_info.api_password and company_info.ip_address and company_info.api_client_id and company_info.api_client_secret and company_info.api_gstin and company_info.api_auth_url and company_info.api_einvoice_url:
            companyno=1
    
            headers = {"Content-Type": "application/json",
                       "username":  company_info.api_username,
                       "password": company_info.api_password,
                       "ip_address": company_info.ip_address,
                       "client_id": company_info.api_client_id,
                       "client_secret": company_info.api_client_secret,
                       "gstin": company_info.api_gstin}
    
            url =  company_info.api_auth_url
    
            json_data = {}
    
            response = requests.get(url, headers=headers)
            response_content = json.loads(response.content)
            if response_content['status_cd']=='Sucess':
                company_info.update({"auth_token":response_content['data']['AuthToken']})
    
            else:
                raise UserError("E-Invoice not successful authentication")
    
            headers = {"Content-Type": "application/json",
                       "username":  company_info.api_username,
                       "auth-token": company_info.auth_token,
                       "ip_address": company_info.ip_address,
                       "client_id": company_info.api_client_id,
                       "client_secret": company_info.api_client_secret,
                       "gstin": company_info.api_gstin}
    
            url =  company_info.api_einvoice_url
            
        if journalno != 1 and companyno != 1:
            if not  company_info.api_username or journal_info.api_username:
                raise UserError ("E-Invoice User Name not set in company or journal")
    
            if not  company_info.api_password or journal_info.api_password:
                raise UserError ("E-Invoice Password not set in company or journal")
    
            if not  company_info.ip_address or journal_info.ip_address:
                raise UserError ("E-Invoice IP Address not set in company or journal")
    
            if not  company_info.api_client_id or journal_info.api_client_id:
                raise UserError ("E-Invoice Client ID not set in company or journal")
    
            if not  company_info.api_client_secret or journal_info.api_client_secret:
                raise UserError ("E-Invoice Client Secret not set in company or journal")
    
            if not  company_info.api_gstin or journal_info.api_gstin:
                raise UserError ("E-Invoice Gstin not set in company or journal")
    
            if not  company_info.api_auth_url or journal_info.api_auth_url:
                raise UserError ("E-invoice Auth URl not set in company or journal")
    
            if not  company_info.api_einvoice_url or journal_info.api_einvoice_url:
                raise UserError ("E-invoice Generate URl not set in company or journal")

        result_list = []
        for rec in self:
            [form_data] = rec.read()
            data = {'form': form_data}
            formData = data['form']
            company = False
            if formData['company_id'][0]:
                company = self.env['res.company'].browse(formData['company_id'][0])

            partner = False
            if formData['partner_id'][0]:
                partner = self.env['res.partner'].browse(formData['partner_id'][0])

            price_precision = self.env['decimal.precision'].precision_get('gst_reporting_price_precision')
            prod_uom_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            response_data = OrderedDict()
            response_data['Version'] = '1.1'
            bill_list_array = []
            TranDtls = OrderedDict()
            DocDtls = OrderedDict()
            SellerDtls = OrderedDict()
            BuyerDtls = OrderedDict()
            DispDtls = OrderedDict()
            ShipDtls = OrderedDict()
            ValDtls = OrderedDict()
            PayDtls = OrderedDict()

            # ------------------- TranDtls -----------------#
            if formData['l10n_in_gst_treatment'] == 'overseas':
                TranDtls = {
                    "TaxSch": "GST",
                    "SupTyp": "EXPWOP",
                    "RegRev": "N",
                    "IgstOnIntra": "N",
                    "EcmGstin": None
                }
            else:
                TranDtls = {
                    "TaxSch": "GST",
                    "SupTyp": "B2B",
                    "RegRev": "N",
                    "IgstOnIntra": "N",
                    "EcmGstin": None
                }

            # ------------------- DocDtls -----------------#
            Typ = ''

            if formData['move_type']:
                if formData['move_type'] in ('in_invoice', 'out_invoice'):
                    Typ = 'INV'
                elif formData['move_type'] == 'out_refund':
                    Typ = 'CRN'
                elif formData['move_type'] in ['in_refund', 'in_refund_sale']:
                    Typ = 'DBN'
                else:
                    Typ = 'INV'
            else:
                Typ = 'INV'

            DocDtls['Typ'] = Typ or "INV"
            invoice_number = (formData['name'] or "")
            DocDtls['No'] = invoice_number
            docDate = ""
            if formData['invoice_date']:
                docDate = formData['invoice_date']
                docDate = datetime.strptime(str(formData['invoice_date']),
                                            DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")
            DocDtls['Dt'] = docDate

            SellerDtls = {}
            SellerDtls['Gstin'] = company and company.partner_id.vat or ""

            SellerDtls['LglNm'] = company and company.name or ""
            company_address = company and company.partner_id.street or ""
            invoice = self.env['account.move'].browse(formData['id'])
            SellerDtls['Addr1'] = company_address
            if company and company.partner_id.street2:
                SellerDtls['Addr2'] = company and company.partner_id.street2
            SellerDtls['Loc'] = company and company.partner_id.city or ""
            SellerDtls['Pin'] = company and int(company.zip) or ""
            SellerDtls['Stcd'] = company and company.state_id.gst_code or "32"
            SellerDtls['Ph'] = None
            SellerDtls['Em'] = None

            BuyerDtls['LglNm'] = partner and partner.name or ""

            partner_shipping_id = False
            if formData['partner_shipping_id'][0]:
                partner_shipping_id = self.env['res.partner'].browse(formData['partner_shipping_id'][0])
            partner_address = partner_shipping_id and partner_shipping_id.street or ""
            BuyerDtls['Addr1'] = partner_address
            if partner_shipping_id and partner_shipping_id.street2:
                BuyerDtls['Addr2'] = partner_shipping_id and partner_shipping_id.street2 or ""
            BuyerDtls['Loc'] = partner_shipping_id and partner_shipping_id.city or ""
            BuyerDtls['POS'] = partner_shipping_id and partner_shipping_id.state_id.gst_code or ""
            if formData['l10n_in_gst_treatment'] == 'overseas':
                BuyerDtls['Pin'] = 999999
                BuyerDtls['Stcd'] = '96'
                BuyerDtls['Gstin'] = 'URP'
                BuyerDtls['POS'] = '96'
            else:
                BuyerDtls['Gstin'] = partner and partner.vat or ""
                BuyerDtls['Pin'] = partner_shipping_id and int(partner_shipping_id.zip) or ""
                BuyerDtls['Stcd'] = partner_shipping_id and partner_shipping_id.state_id.gst_code or "32"
                BuyerDtls['POS'] = partner_shipping_id and partner_shipping_id.state_id.gst_code or ""
            BuyerDtls['Ph'] = None
            BuyerDtls['Em'] = None
            EwbDtls = OrderedDict()
            EwbDtls['TransMode'] = formData['eway_transportation_mode'] and str(formData['eway_transportation_mode']) or None
            EwbDtls['Distance'] = formData['eway_distance'] and int(formData['eway_distance']) or 0
            EwbDtls['TransName'] = formData['eway_transporter'] and str(formData['eway_transporter'][1]) or None
            EwbDtls['TransId'] = formData['eway_transporter_id'] and str(formData['eway_transporter_id']) or None
            EwbDtls['VehType'] = formData['eway_transporter_type'] and str(formData['eway_transporter_type']) or None
            EwbDtls['TransDocNo'] = formData['eway_transport_doc_no'] and str(formData['eway_transport_doc_no']) or ""
            EwbDtls['VehNo'] = formData['eway_vehicle_no'] and str(formData['eway_vehicle_no']) or ""
            RefDtls = {"InvRm": "NICGEPP"}


            total_taxable_value = 0.00
            total_inv_value = 0.00
            total_cgst_amount = 0.00
            total_sgst_amount = 0.00
            total_igst_amount = 0.00
            total_tcs_amount = 0.00
            ItemList = []
            main_hsn_code = ""
            inv_discount = 0.00
            for acc_inv in self.env['account.move'].browse(formData['id']):
                item_no = 0
                total_inv_value = round(acc_inv.amount_total)
                total_tcs_amount = 0


                for line in acc_inv.invoice_line_ids:

                    line_total = 0.0
                    taxable_value = 0.0
                    total_value = 0.0
                    item_dict = {}

                    total_cgst_amount = round((total_cgst_amount + (line.cgst_amount or 0.00)), price_precision)
                    total_sgst_amount = round((total_sgst_amount + (line.sgst_amount or 0.00)), price_precision)
                    total_igst_amount = round((total_igst_amount + (line.igst_amount or 0.00)), price_precision)
# 
                    taxable_value = round((line.price_subtotal or 0.00), price_precision)
                    total_value = round((line.price_subtotal or 0.00), price_precision)
                    price_unit = round((line.price_unit or 0.00), price_precision)
                    total_taxable_value = round((total_taxable_value + taxable_value), price_precision)
                    line_total = round(line.price_total or 0.00,price_precision)
                    inv_value = round((line.price_total or 0.00), price_precision)
                    igst_rate = 0
                    cgst_rate = 0
                    sgst_rate = 0
                    for tax in line.tax_ids:
                        tax_percentage = tax.amount
                        if isinstance(tax_percentage, float):
                            if tax_percentage.is_integer():
                                tax_percentage = int(tax_percentage)
                            else:
                                tax_percentage = round(tax_percentage, 2)
                        if tax.tax_group_id.name == "IGST":
                            igst_rate += tax_percentage
                        elif tax.tax_group_id.name == "GST":
                            cgst_rate += tax_percentage/2 
                            sgst_rate += tax_percentage/2

                    hsn_code = ""
                    if line.product_id:
                        hsn_code = line.product_id.l10n_in_hsn_code or ''

                    if not main_hsn_code and hsn_code:
                        main_hsn_code = hsn_code

                    item_no += 1
                    item_dict['SlNo'] = str(item_no) or ""
                    item_dict['PrdDesc'] = line and line.name or ""
                    if line.product_id.type == 'service':
                        item_dict['IsServc'] = "Y"
                    else:
                        item_dict['IsServc'] = "N"
                    item_dict['HsnCd'] = hsn_code
                    if prod_uom_precision == 0:
                        item_dict['Qty'] = int(round((line and line.quantity or 0), prod_uom_precision))
                    else:
                        item_dict['Qty'] = round((line and line.quantity or 0), prod_uom_precision)

                    item_dict['Unit'] = line.product_uom_id.l10n_in_code or ''

                    item_dict['UnitPrice'] = round(price_unit, price_precision) or 0.00
                    item_dict['TotAmt'] = total_value
                    item_dict['Discount'] = 0.00
                    item_dict['PreTaxVal'] = taxable_value
                    item_dict['AssAmt'] = taxable_value
                    item_dict['GstRt'] = sgst_rate + cgst_rate + igst_rate
                    item_dict['IgstAmt'] = round(line.igst_amount, price_precision) or 0.00
                    item_dict['CgstAmt'] = round(line.cgst_amount, price_precision) or 0.00
                    item_dict['SgstAmt'] = round(line.sgst_amount, price_precision) or 0.00
                    item_dict['CesRt'] = 0
                    item_dict['CesAmt'] = 0
                    item_dict['CesNonAdvlAmt'] = 0
                    item_dict['StateCesRt'] = 0
                    item_dict['StateCesAmt'] = 0
                    item_dict['StateCesNonAdvlAmt'] = 0
                    item_dict['OthChrg'] = 0
                    item_dict['TotItemVal'] = line_total or 0.00

                    ItemList.append(item_dict)
            ValDtls['AssVal'] = total_taxable_value
            ValDtls['IgstVal'] = total_igst_amount
            ValDtls['CgstVal'] = total_cgst_amount
            ValDtls['SgstVal'] = total_sgst_amount
            ValDtls['CesVal'] = 0.00
            ValDtls['StCesVal'] = 0.00
            ValDtls['CesVal'] = 0.00
            ValDtls['Discount'] = 0.00
            ValDtls['CesVal'] = 0.00
            ValDtls['OthChrg'] = -1 * total_tcs_amount if total_tcs_amount < 0 else total_tcs_amount
            ValDtls['RndOffAmt'] = 0.00
            ValDtls['TotInvVal'] = total_inv_value
            response_data['TranDtls'] = TranDtls
            response_data['DocDtls'] = DocDtls
            response_data['SellerDtls'] = SellerDtls
            response_data['BuyerDtls'] = BuyerDtls
            response_data['ValDtls'] = ValDtls
            response_data['ItemList'] = ItemList
            result_list.append(response_data)
            response = requests.post(url, data=json.dumps(dict(response_data)), headers=headers)

            response_content = json.loads(response.content)

            if response_content['status_cd']=='1':
                rec.update({"ack_no":response_content['data']['AckNo'],
                            "ack_date":response_content['data']['AckDt'],
                            "irn":response_content['data']['Irn'],
                            "ewb_no":response_content['data']['EwbNo'],
                            "scaned_qr_code":response_content['data']['SignedQRCode'],
                            "einvoice_generated" : True
                             })

            else:
                if response_content['status_cd']=='0':
                    raise UserError (response_content['status_desc'])

    def create_eway_bill_from_gst_portal(self):

        companyno=0
        journalno=0
        company_info = self.company_id
        journal_info = self.journal_id
        
        if journal_info.eway_username and journal_info.eway_password and journal_info.eway_ip_address and journal_info.eway_client_id and journal_info.eway_client_secret and journal_info.eway_gstin and journal_info.eway_auth_url and journal_info.eway_generate_url:
            journalno = 1 
            
            
            headers = {"Content-Type": "application/json",
                   "ip_address": journal_info.eway_ip_address,
                   "client_id": journal_info.eway_client_id,
                   "client_secret": journal_info.eway_client_secret,
                   "gstin": journal_info.eway_gstin}

            url =  journal_info.eway_auth_url
    
            json_data = {}
    
            response = requests.get(url, headers=headers)
            response_content = json.loads(response.content)
            if response_content['status_cd']=='0':
                raise UserError("E-Way Bill not successful authentication")
    
            headers = {"Content-Type": "application/json",
                       "ip_address": journal_info.eway_ip_address,
                       "client_id": journal_info.eway_client_id,
                       "client_secret": journal_info.eway_client_secret,
                       "gstin": journal_info.eway_gstin}
    
    
            url =  journal_info.eway_generate_url
    
            
        elif company_info.eway_username and company_info.eway_password and company_info.eway_ip_address and company_info.eway_client_id and company_info.eway_client_secret and company_info.eway_gstin and company_info.eway_auth_url and company_info.eway_generate_url:
            companyno=1
    
            headers = {"Content-Type": "application/json",
                   "ip_address": company_info.eway_ip_address,
                   "client_id": company_info.eway_client_id,
                   "client_secret": company_info.eway_client_secret,
                   "gstin": company_info.eway_gstin}

            url =  company_info.eway_auth_url
    
            json_data = {}
    
            response = requests.get(url, headers=headers)
            response_content = json.loads(response.content)
            if response_content['status_cd']=='0':
                raise UserError("E-Way Bill not successful authentication")
    
            headers = {"Content-Type": "application/json",
                       "ip_address": company_info.eway_ip_address,
                       "client_id": company_info.eway_client_id,
                       "client_secret": company_info.eway_client_secret,
                       "gstin": company_info.eway_gstin}
    
            url =  company_info.eway_generate_url
            
        if journalno != 1 and companyno != 1:
            if not  company_info.eway_username or journal_info.eway_username:
                raise UserError ("E-Way User Name not set in company or journal")
    
            if not  company_info.eway_password or journal_info.eway_password:
                raise UserError ("E-Way Password not set in company or journal")
    
            if not  company_info.eway_ip_address or journal_info.eway_ip_address:
                raise UserError ("E-Way IP Address not set in company or journal")
    
            if not  company_info.eway_client_id or journal_info.eway_client_id:
                raise UserError ("E-Way Client ID not set in company or journal")
    
            if not  company_info.eway_client_secret or journal_info.eway_client_secret:
                raise UserError ("E-Way Client Secret not set in company or journal")
    
            if not  company_info.eway_gstin or journal_info.eway_gstin:
                raise UserError ("E-Way Gstin not set in company or journal")
    
            if not  company_info.eway_auth_url or journal_info.eway_auth_url:
                raise UserError ("E-Way Auth URl not set in company or journal")
    
            if not  company_info.eway_generate_url or journal_info.eway_generate_url:
                raise UserError ("E-Way Generate URl not set in company or journal")

        result_list = []
        for rec in self:
            if rec.eway_bill_no:
                raise UserError ("E-way already generated")  
            [form_data] = rec.read()
            data = {'form': form_data}
            formData = data['form']
            company = False
            if formData['company_id'][0]:
                company = self.env['res.company'].browse(formData['company_id'][0])
            #
            partner = False
            if formData['partner_id'][0]:
                partner = self.env['res.partner'].browse(formData['partner_id'][0])
            #
            partner_shipping_id = False
            if formData['partner_shipping_id'][0]:
                partner_shipping_id = self.env['res.partner'].browse(formData['partner_shipping_id'][0])
            partner_address = partner_shipping_id and partner_shipping_id.street or ""
            #
            price_precision = self.env['decimal.precision'].precision_get('gst_reporting_price_precision')
            prod_uom_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            response_data = OrderedDict()
            response_data['supplyType'] = formData['eway_supply_type'] and str(formData['eway_supply_type']) or "I"
            response_data['subSupplyType'] = formData['eway_sub_supply_type'] and str(formData['eway_sub_supply_type']) or ""
            response_data['subSupplyDesc'] = formData['eway_sub_supply_desc'] and str(formData['eway_sub_supply_desc']) or ""
            if formData['move_type']:
                if formData['move_type'] in ('in_invoice', 'out_invoice'):
                    Typ = 'INV'
                elif formData['move_type'] == 'out_refund':
                    Typ = 'CRN'
                elif formData['move_type'] in ['in_refund', 'in_refund_sale']:
                    Typ = 'DBN'
                else:
                    Typ = 'INV'
            else:
                Typ = 'INV'

            response_data['docType'] = formData['eway_document_type'] and str(formData['eway_document_type']) or ""

            if formData['invoice_date']:
                docDate = formData['invoice_date']
                docDate = datetime.strptime(str(formData['invoice_date']),
                                            DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")

            response_data['docDate'] = docDate

            invoice_number = (formData['name'] or "")
            response_data['docNo'] = invoice_number

            response_data['fromGstin'] = company and company.eway_gstin or journal_info.eway_gstin or ""
            response_data['fromStateCode'] = company and int(company.state_id.gst_code) or "32"
            response_data['actFromStateCode'] = company and int(company.state_id.gst_code) or ""
            response_data['fromTrdName'] = company and company.name or ""
            company_address = company and company.partner_id.street or ""
            response_data['fromAddr1'] = company_address
            if company and company.partner_id.street2:
                response_data['fromAddr2'] = company and company.partner_id.street2
            response_data['fromPlace'] = company and company.partner_id.city or ""
            response_data['fromPincode'] = company and int(company.zip) or ""

            response_data['toGstin'] = partner and partner.vat or ""
            response_data['toStateCode'] = partner and int(partner.state_id.gst_code) or "32"
            response_data['actToStateCode'] = partner and int(partner.state_id.gst_code) or ""
            response_data['toTrdName'] = partner and partner.name or ""
            response_data['toAddr1'] = partner_address
            if partner_shipping_id and partner_shipping_id.street2:
                response_data['toAddr2'] = partner_shipping_id and partner_shipping_id.street2 or ""
            response_data['toPlace'] = partner_shipping_id and partner_shipping_id.city or ""
            response_data['toPincode'] = partner_shipping_id and int(partner_shipping_id.zip) or ""
            response_data['shipToGSTIN'] = partner_shipping_id and partner_shipping_id.vat or ""
            response_data['shipToTradeName'] = partner_shipping_id and partner_shipping_id.name or ""
            response_data['transactionType'] = formData['transaction_type'] and int(formData['transaction_type']) or ""
            response_data['dispatchFromGSTIN'] = company and company.partner_id.vat or ""
            response_data['dispatchFromTradeName'] = company and company.name or ""

            total_taxable_value = 0.00
            total_inv_value = 0.00
            total_cgst_amount = 0.00
            total_sgst_amount = 0.00
            total_igst_amount = 0.00
            total_tcs_amount = 0.00
            ItemList = []
            main_hsn_code = ""
            inv_discount = 0.00
            for acc_inv in self.env['account.move'].browse(formData['id']):
                item_no = 0
                total_inv_value = round(acc_inv.amount_total)
                # total_tcs_amount = acc_inv.tcs_amount
                total_tcs_amount = 0


                for line in acc_inv.invoice_line_ids:

                    line_total = 0.0
                    taxable_value = 0.0
                    total_value = 0.0
                    item_dict = {}

                    total_cgst_amount = round((total_cgst_amount + (line.cgst_amount or 0.00)), price_precision)
                    total_sgst_amount = round((total_sgst_amount + (line.sgst_amount or 0.00)), price_precision)
                    total_igst_amount = round((total_igst_amount + (line.igst_amount or 0.00)), price_precision)
#                     
                    taxable_value = round((line.price_subtotal or 0.00), price_precision)
                    total_value = round((line.price_subtotal or 0.00), price_precision)
                    price_unit = round((line.price_unit or 0.00), price_precision)
                    total_taxable_value = round((total_taxable_value + taxable_value), price_precision)
                    line_total = round(line.price_total or 0.00,price_precision)
                    inv_value = round((line.price_total or 0.00), price_precision)
                    igst_rate = 0
                    cgst_rate = 0
                    sgst_rate = 0
                    for tax in line.tax_ids:
                        tax_percentage = tax.amount
                        if isinstance(tax_percentage, float):
                            if tax_percentage.is_integer():
                                tax_percentage = int(tax_percentage)
                            else:
                                tax_percentage = round(tax_percentage, 2)
                        if tax.tax_group_id.name == "IGST":
                            igst_rate += tax_percentage
                        elif tax.tax_group_id.name == "GST":
                            cgst_rate += tax_percentage/2 
                            sgst_rate += tax_percentage/2

                    hsn_code = ""
                    if line.product_id:
                        hsn_code = line.product_id.l10n_in_hsn_code or ''

                    if not main_hsn_code and hsn_code:
                        main_hsn_code = hsn_code

                    item_no += 1

                    item_dict['productName'] = line and line.product_id.name or ""
                    item_dict['ProductDesc'] = line and line.name or ""
                    item_dict['hsnCode'] = hsn_code
                    if prod_uom_precision == 0:
                        item_dict['quantity'] = int(round((line and line.quantity or 0), prod_uom_precision))
                    else:
                        item_dict['quantity'] = round((line and line.quantity or 0), prod_uom_precision)

                    item_dict['qtyUnit'] = line.product_uom_id.l10n_in_code or ''
                    item_dict['taxableAmount'] = taxable_value


                    igst_rate = round(line.igst_amount, price_precision) or 0.00
                    if igst_rate == 0.00:
                        rate_igst = 0
                    else:
                        rate_igst = (igst_rate*100)/taxable_value

                    cgst_rate = round(line.cgst_amount, price_precision) or 0.00
                    if cgst_rate == 0.00:
                        rate_cgst = 0
                    else:
                        rate_cgst = (cgst_rate*100)/taxable_value

                    sgst_rate = round(line.sgst_amount, price_precision) or 0.00
                    if sgst_rate == 0.00:
                        rate_sgst = 0
                    else:
                        rate_sgst = (sgst_rate*100)/taxable_value


                    item_dict['igstRate'] = rate_igst
                    item_dict['cgstRate'] = rate_cgst
                    item_dict['sgstRate'] = rate_sgst


                    item_dict['cessRate'] = 0

                    ItemList.append(item_dict)

            response_data['totalValue'] = total_taxable_value
            response_data['igstValue'] = total_igst_amount
            response_data['cgstValue'] = total_cgst_amount
            response_data['sgstValue'] = total_sgst_amount
            response_data['cessValue'] = 0.00
            response_data['cessNonAdvolValue'] = 0.00
            response_data['totInvValue'] = total_inv_value


            response_data['transMode'] = formData['eway_transportation_mode'] and str(formData['eway_transportation_mode']) or ""

            if formData['eway_distance']:
                response_data['transDistance'] = formData['eway_distance'] and str(formData['eway_distance']) or ""
            else:
                response_data['transDistance'] = "0"

            response_data['transporterName'] = formData['eway_transporter'] and str(formData['eway_transporter'][1]) or ""

            if formData['eway_transporter_id']:
                response_data['transporterId'] = formData['eway_transporter_id'] and str(formData['eway_transporter_id']) or ""
            else:
                response_data['transporterId'] =  company_info.api_gstin

            transDocDate = ""
            if formData['eway_transport_date']:
                transDocDate = datetime.strptime(str(formData['eway_transport_date']),
                                            DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")

            response_data['transDocNo'] = formData['eway_transport_doc_no'] and str(formData['eway_transport_doc_no']) or ""
            response_data['transDocDate'] = transDocDate
            response_data['vehicleNo'] = formData['eway_vehicle_no'] and str(formData['eway_vehicle_no']) or ""
            response_data['vehicleType'] = formData['eway_transporter_type'] and str(formData['eway_transporter_type']) or ""
            response_data['itemList'] = ItemList

            result_list.append(response_data)
            response = requests.post(url, data=json.dumps(dict(response_data)), headers=headers)
            response_content = json.loads(response.content)

            if response_content['status_cd']=='0':
                raise UserError(response_content['error']['message'])

            else:
                rec.update({
                    "eway_bill_no":response_content['data']['ewayBillNo'],
                    "eway_bill_date":response_content['data']['ewayBillDate'],
                    "eway_bill_valid_upto":response_content['data']['validUpto'],

                    })  


    def fetch_irn_eway_from_gst_portal(self):
        
        companyno=0
        journalno=0
        company_info = self.company_id
        journal_info = self.journal_id
        
        if journal_info.api_username and journal_info.api_password and journal_info.ip_address and journal_info.api_client_id and journal_info.api_client_secret and journal_info.api_gstin and journal_info.api_auth_url and journal_info.api_einvoice_url:
            journalno = 1
        
            headers = {"Content-Type": "application/json",
                       "username":  journal_info.api_username,
                       "password": journal_info.api_password,
                       "ip_address": journal_info.ip_address,
                       "client_id": journal_info.api_client_id,
                       "client_secret": journal_info.api_client_secret,
                       "gstin": journal_info.api_gstin}
    
            url =  journal_info.api_auth_url
    
            json_data = {}
    
            response = requests.get(url, headers=headers)
            response_content = json.loads(response.content)
            if response_content['status_cd']=='Sucess':
                journal_info.update({"auth_token":response_content['data']['AuthToken']})
    
            else:
                raise UserError("E-way not successful authentication")
    
            headers = {"Content-Type": "application/json",
                       "username":  journal_info.api_username,
                       "auth-token": journal_info.auth_token,
                       "ip_address": journal_info.ip_address,
                       "client_id": journal_info.api_client_id,
                       "client_secret": journal_info.api_client_secret,
                       "gstin": journal_info.api_gstin}
    
            url =  journal_info.eway_irn_generate_url

        elif company_info.api_username and company_info.api_password and company_info.ip_address and company_info.api_client_id and company_info.api_client_secret and company_info.api_gstin and company_info.api_auth_url and company_info.api_einvoice_url:
            companyno=1
            
            headers = {"Content-Type": "application/json",
                       "username":  company_info.api_username,
                       "password": company_info.api_password,
                       "ip_address": company_info.ip_address,
                       "client_id": company_info.api_client_id,
                       "client_secret": company_info.api_client_secret,
                       "gstin": company_info.api_gstin}
    
            url =  company_info.api_auth_url
    
            json_data = {}
    
            response = requests.get(url, headers=headers)
            response_content = json.loads(response.content)
            if response_content['status_cd']=='Sucess':
                company_info.update({"auth_token":response_content['data']['AuthToken']})
    
            else:
                raise UserError("E-way not successful authentication")
    
            headers = {"Content-Type": "application/json",
                       "username":  company_info.api_username,
                       "auth-token": company_info.auth_token,
                       "ip_address": company_info.ip_address,
                       "client_id": company_info.api_client_id,
                       "client_secret": company_info.api_client_secret,
                       "gstin": company_info.api_gstin}

            url =  company_info.eway_irn_generate_url
            
        result_list = []
        for rec in self:
            if rec.eway_bill_no:
                raise UserError ("E-way already generated")   
            
            if not rec.irn:
                raise UserError ("Irn not set in invoice")   
            
            if not rec.eway_transportation_mode:
                raise UserError ("Transportation mode not set in invoice") 
            
            
            if not rec.eway_transport_date:
                raise UserError ("Transport Date not set in invoice") 
            
            if not rec.eway_vehicle_no:
                raise UserError ("Vehicle No not set in invoice") 
            
            if not rec.eway_transporter_type:
                raise UserError ("Transporter Type not set in invoice")
            
            [form_data] = rec.read()
            data = {'form': form_data}
            formData = data['form']
            company = False
#  
            response_data = OrderedDict()

            response_data['Irn'] = formData['irn'] and str(formData['irn']) or ""
            response_data['Distance'] = formData['eway_distance'] and formData['eway_distance'] or 0
            response_data['TransMode'] = formData['eway_transportation_mode'] and str(formData['eway_transportation_mode']) or ""

            if formData['eway_transporter_id']:
                response_data['TransId'] = formData['eway_transporter_id'] and str(formData['eway_transporter_id']) or ""
            else:
                response_data['TransId'] =  journal_info.api_gstin if journal_info.api_gstin else company_info.api_gstin

            if formData['eway_transporter']:
                response_data['TransName'] = formData['eway_transporter'] and str(formData['eway_transporter'][1]) or ""
            else:
                response_data['TransName'] =  company_info.partner_id.name

            transDocDate = ""
            if formData['eway_transport_date']:
                transDocDate = datetime.strptime(str(formData['eway_transport_date']),
                                                 DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y")

            response_data['TransDocDt'] = transDocDate

            if formData['eway_transport_doc_no']:
                response_data['TransDocNo'] = formData['eway_transport_doc_no'] and str(formData['eway_transport_doc_no']) or ""
            else:
                response_data['TransDocNo'] = formData['name']
            response_data['VehNo'] = formData['eway_vehicle_no'] and str(formData['eway_vehicle_no']) or ""
            response_data['VehType'] = formData['eway_transporter_type'] and str(formData['eway_transporter_type']) or ""



            result_list.append(response_data)
            response = requests.post(url, data=json.dumps(dict(response_data)), headers=headers)
            response_content = json.loads(response.content)

            if response_content['status_cd']=='0':
                raise UserError(response_content['status_desc'])

            else:
                rec.update({
                    "eway_bill_no":response_content['data']['EwbNo'],
                    "eway_bill_date":response_content['data']['EwbDt'],
                    "eway_bill_valid_upto":response_content['data']['EwbValidTill'],

                    })
                
    def get_gst_tax(self,line):
        tax_list =[]
        join_tax =''
        if line:
            for tax in line:
                tax_list.append(tax.name)
                join_tax = ", ".join(tax_list)
        return join_tax
    
    def get_tax_grouped(self):
        values = {}
        for rec in self:

            for line in rec.invoice_line_ids:
                val = {
                    'hsn_code': line.product_id.l10n_in_hsn_code,
                    'taxable_value': line.price_subtotal,
                    'line_tax': rec.currency_id.round(line.price_total - line.price_subtotal),
                }
                if line.igst_amount > 0:
                    val.update({
                        'cgst_rate': '',
                        'cgst_amt': line.cgst_amount,
                        'sgst_rate': '',
                        'sgst_amt': line.sgst_amount,
                        'igst_rate': line.tax_ids[0].amount if line.tax_ids else '',
                        'igst_amt': line.igst_amount,
                    })
                else:
                    value = []
                    if line.tax_ids:
                        for tax in line.tax_ids[0].children_tax_ids:
                            value.append(tax.amount)
                    val.update({
                        'cgst_rate': value[0] if value else '',
                        'cgst_amt': line.cgst_amount,
                        'sgst_rate': value[1] if len(value) > 1 else '',
                        'sgst_amt': line.sgst_amount,
                        'igst_rate': '',
                        'igst_amt': line.igst_amount,
                    })
                if line.product_id.l10n_in_hsn_code not in values:
                    values.update({line.product_id.l10n_in_hsn_code: val})
                else:
                    taxable_value = values[line.product_id.l10n_in_hsn_code].get('taxable_value', 0) + \
                                    val['taxable_value']
                    line_tax = values[line.product_id.l10n_in_hsn_code].get('line_tax', 0) + \
                                    val['line_tax']
                    cgst_amt = values[line.product_id.l10n_in_hsn_code].get('cgst_amt', 0) + val['cgst_amt']
                    sgst_amt = values[line.product_id.l10n_in_hsn_code].get('sgst_amt', 0) + val['sgst_amt']
                    igst_amt = values[line.product_id.l10n_in_hsn_code].get('igst_amt', 0) + val['igst_amt']
                    values[line.product_id.l10n_in_hsn_code].update({
                        'cgst_amt': cgst_amt,
                        'sgst_amt': sgst_amt,
                        'igst_amt': igst_amt,
                        'taxable_value': taxable_value,
                        'line_tax': line_tax,
                    })
            return list(values.values())
