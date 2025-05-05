# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2023 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>)
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

import xmlrpc
import logging
import json
import requests
import datetime
import pytz
import re
import sys
import requests
from datetime import datetime
from dateutil import parser
from odoo import models, fields, api, _
from odoo import http
from odoo.http import request
from requests import Response
from odoo import tools
from _ldap import ALREADY_EXISTS
from odoo.addons.web.controllers.session import Session
#from uaclient.api.u import pro
import random
from collections import defaultdict
import base64
from werkzeug.urls import url_parse
_logger = logging.getLogger(__name__)

            

class PartnerLedgerPdfController(http.Controller):
    
    @http.route(['/api/partner_ledger_json'], type='json', auth='public', methods=['POST'], csrf=False, cors="*")
    def partner_ledger_json(self, **post):
        try:
            from_date = post.get('from_date')
            to_date = post.get('to_date')
            partner_ids = post.get('partner_ids')
            move_type_dict = dict(request.env['account.move']._fields['move_type'].selection)
            partner_ledger = request.env['partner.ledger.wiz'].sudo().create({
            'from_date': from_date,
            'to_date': to_date,
            'partner_ids': partner_ids,
        })
        
            partner_ledger.load_data()
            ledger_data = []
            for line in partner_ledger.partner_ledger_line_ids:
                move_line = line.move_line_id
                name =  None
                move = move_line.move_id
    
                related_id = None
                if move:
                    related_id = move.id
                    name = move_type_dict.get(move.move_type, move.move_type)
                if move.origin_payment_id:
                    payment = move.origin_payment_id
                    related_id = payment.id
                    if payment.payment_type == 'outbound':
                        name = "Payment"
                    elif payment.payment_type == 'inbound':
                        name = "Receipt"
                ledger_data.append({
                    'id': related_id,
                    'name': name,
           # 'journal_type': line.move_line_id.journal_id.type,
			        'date': from_date if line.ref == 'Opening Balance' else (line.date or ''),
			        'ref': line.ref or '',
			        'debit': line.debit,
			        'credit': line.credit,
			        'balance': line.balance,
			    })
            
            return {
                'data': ledger_data
            }
    
        except Exception as e:
            return {
                'errormessage': "Internal Server Error",
                'errorcode': 500,
                'data': None,
                'error': str(e)
            }

    @http.route(['/api/partner_ledger_pdf'], type='json', auth='public', methods=['POST'], csrf=False, cors="*")
    def partner_ledger_pdf(self, **post):
        try:
            from_date = post.get('from_date')
            to_date = post.get('to_date')
            partner_ids = post.get('partner_ids')            
            partner_ledger = request.env['partner.ledger.wiz'].sudo().create({
            'from_date': from_date,
            'to_date': to_date,
            'partner_ids': [(6, 0, partner_ids)],             
        })
            
            
            report_name = 'zb_financial_reports.partner_ledger_reports'
            pdf, _ = request.env['ir.actions.report']._render_qweb_pdf(report_name, [partner_ledger.id])
            
    
            pdf_base64 = base64.b64encode(pdf)
    
            base_url = http.request.httprequest.base_url
            parsed_url = url_parse(base_url)
            base_url = parsed_url.scheme + '://' + parsed_url.netloc
    
            attachment = request.env['ir.attachment'].sudo().create({
                'name': f'Partner Ledger Report.pdf',
                'datas': pdf_base64.decode('utf-8'),
                'res_model': 'partner.ledger.wiz',
                'res_id': partner_ledger.id,
                'type': 'binary',
                'mimetype': 'application/pdf',
                'access_token': request.env['ir.attachment']._generate_access_token(),
            })
            attachment_url = f'{base_url}/web/content/{attachment.id}?access_token={attachment.access_token}&download=true'
            return {
                'errormessage': "PDF URL Generated Successfully",
                'errorcode': 200,
                'data': {
                    'pdf_url': attachment_url
                }
            }
    
        except Exception as e:
            return {
                'errormessage': "Internal Server Error",
                'errorcode': 500,
                'data': None,
                'error': str(e)
            }

    @http.route(['/api/balance_confimation_pdf'], type='json', auth='public', methods=['POST'], csrf=False, cors="*")
    def balance_confirmation_pdf(self, **post):
        try:
            date = post.get('date')
            partner_ids = post.get('partner_ids')            
            balance_confirmation = request.env['balance.confirmation.wiz'].sudo().create({
            'date': date,
            'partner_ids': partner_ids,            
        })
            
            
            report_name = 'zb_financial_reports.action_balance_confirmation_saudi'
            pdf, _ = request.env['ir.actions.report']._render_qweb_pdf(report_name, [balance_confirmation.id])
    
            pdf_base64 = base64.b64encode(pdf)
    
            base_url = http.request.httprequest.base_url
            parsed_url = url_parse(base_url)
            base_url = parsed_url.scheme + '://' + parsed_url.netloc
    
            attachment = request.env['ir.attachment'].sudo().create({
                'name': f'Balance Confirmation Report.pdf',
                'datas': pdf_base64.decode('utf-8'),
                'res_model': 'balance.confirmation.wiz',
                'res_id': balance_confirmation.id,
                'type': 'binary',
                'mimetype': 'application/pdf',
                'access_token': request.env['ir.attachment']._generate_access_token(),
            })
            attachment_url = f'{base_url}/web/content/{attachment.id}?access_token={attachment.access_token}&download=true'
            return {
                'errormessage': "PDF URL Generated Successfully",
                'errorcode': 200,
                'data': {
                    'pdf_url': attachment_url
                }
            }
    
        except Exception as e:
            return {
                'errormessage': "Internal Server Error",
                'errorcode': 500,
                'data': None,
                'error': str(e)
            }

    @http.route(['/api/partner_summary_pdf'], type='json', auth='public', methods=['POST'], csrf=False, cors="*")
    def partner_summary_pdf(self, **post):
        try:
            from_date = post.get('from_date')
            to_date = post.get('to_date')
            partner_summary = request.env['partner.summary.wiz'].sudo().create({
            'from_date': from_date,
            'to_date': to_date,  
        })
            
            partner_summary.customers_for_the_period = True
            partner_summary.account_type = "asset_receivable"
            partner_summary.load_data()            
            report_name = 'zb_financial_reports.action_partner_summary'
            pdf, _ = request.env['ir.actions.report']._render_qweb_pdf(report_name, [partner_summary.id])
            
    
            pdf_base64 = base64.b64encode(pdf)
    
            base_url = http.request.httprequest.base_url
            parsed_url = url_parse(base_url)
            base_url = parsed_url.scheme + '://' + parsed_url.netloc
    
            attachment = request.env['ir.attachment'].sudo().create({
                'name': f'Partner Summary.pdf',
                'datas': pdf_base64.decode('utf-8'),
                'res_model': 'partner.summary.wiz',
                'res_id': partner_summary.id,
                'type': 'binary',
                'mimetype': 'application/pdf',
                'access_token': request.env['ir.attachment']._generate_access_token(),
            })
            attachment_url = f'{base_url}/web/content/{attachment.id}?access_token={attachment.access_token}&download=true'
            return {
                'errormessage': "PDF URL Generated Successfully",
                'errorcode': 200,
                'data': {
                    'pdf_url': attachment_url
                }
            }
    
        except Exception as e:
            return {
                'errormessage': "Internal Server Error",
                'errorcode': 500,
                'data': None,
                'error': str(e)
            }


    @http.route(['/api/ageing_report_pdf'], type='json', auth='public', methods=['POST'], csrf=False, cors="*")
    def ageing_report_pdf(self, **post):
        try:
            date_as_on = post.get('date_as_on')
            ageing_record = request.env['ageing.report.wizard'].sudo().create({
            'date_as_on': date_as_on,
            'account_type' : 'receivable',
        })
            
            ageing_record.onchange_account_type()
            ageing_record.amount = "residual"
            ageing_record.partner_type = "Customer"            
            ageing_record.load_data()            
            report_name = 'zb_financial_reports.action_partner_ageing_report'
            pdf, _ = request.env['ir.actions.report']._render_qweb_pdf(report_name, [ageing_record.id])
            
    
            pdf_base64 = base64.b64encode(pdf)
    
            base_url = http.request.httprequest.base_url
            parsed_url = url_parse(base_url)
            base_url = parsed_url.scheme + '://' + parsed_url.netloc
    
            attachment = request.env['ir.attachment'].sudo().create({
                'name': 'Ageing Report.pdf',
                'datas': pdf_base64.decode('utf-8'),
                'res_model': 'ageing.report.wizard',
                'res_id': ageing_record.id,
                'type': 'binary',
                'mimetype': 'application/pdf',
                'access_token': request.env['ir.attachment']._generate_access_token(),
            })
            attachment_url = f'{base_url}/web/content/{attachment.id}?access_token={attachment.access_token}&download=true'
            return {
                'errormessage': "PDF URL Generated Successfully",
                'errorcode': 200,
                'data': {
                    'pdf_url': attachment_url
                }
            }
    
        except Exception as e:
            return {
                'errormessage': "Internal Server Error",
                'errorcode': 500,
                'data': None,
                'error': str(e)
            }

