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

from odoo import fields, models,api,_
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


class AgeingReportWiazrd(models.TransientModel):

    _name = 'ageing.report.wizard'
    _description = 'Ageing Report Wiazrd'

    amount=fields.Selection([('balance','Balance'),('residual','Residual')],'Amount')
    name = fields.Char('Name',default = 'Ageing Report')
    date_as_on = fields.Date('Date As On',default=fields.Date.today)
    partner_type = fields.Selection([('Customer','Customer'),('Vendor','Vendor')],string="Partner Type")
    account_type = fields.Selection([('receivable','Receivable'),('payable','Payable'),('both','Receivable & Payable')],string="Account Type")
    based_on = fields.Selection([('Date','Date'),('DueDate','Due_date')],string="Based On",default="Date")
    account_ids=fields.Many2many("account.account","account_ageing_rel","account_id","ageing_id",string="Account",domain="['|', ('account_type','=', 'asset_receivable'), ('account_type','=','liability_payable')]")   
    company_id=fields.Many2one("res.company", default=lambda self: self.env.company.id)
    child_company_ids=fields.Many2many("res.company","company_ageing_rel","company_id","ageing_id",string="Child Company")
    partner_ids=fields.One2many("partner.lines","partner_lines_id",string="Partner")
    age_type = fields.Selection([
        ('age_30', '30 Days'),
        ('age_45', '45 Days'),
        ('yearly', 'Yearly'),
    ], string="Age Type", default='age_30')
    partner_category_ids = fields.Many2many(
        "res.partner.category", 
        "partner_category_ageing_rel", 
        "ageing_report_id", 
        "category_id", 
        string="Partner Categories"
    )
    
    # @api.onchange('account_type')
    # def onchange_account_type(self):
    #     for rec in self:
    #         account_ids = False
    #         if rec.account_type:
    #             if rec.account_type == 'receivable':
    #                 account_ids = self.env['account.account'].search([('account_type','=','asset_receivable')])
    #             elif rec.account_type == 'payable':
    #                 account_ids = self.env['account.account'].search([('account_type','=','liability_payable')])
    #             elif rec.account_type == 'both':
    #                 account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
    #         # else:
    #         #     account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
    #         if account_ids:
    #             print("account_ids==================",account_ids,len(account_ids))
    #             #     rec.account_ids = [(6,0,account_ids.ids)]
    #
    #             return {'domain': {'account_ids': [('account_type', '=', 'asset_receivable')]}}
    #
    
    
    @api.onchange('account_type')
    def onchange_account_type(self):
        for rec in self:
            rec.account_ids = False
            account_ids = False
            if rec.account_type:
                if rec.account_type == 'receivable':
                    account_ids = self.env['account.account'].search([('account_type','=','asset_receivable')])
                elif rec.account_type == 'payable':
                    account_ids = self.env['account.account'].search([('account_type','=','liability_payable')])
                elif rec.account_type == 'both':
                    account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
            # else:
            #     account_ids = self.env['account.account'].search([('account_type','in',['asset_receivable','liability_payable'])])
                if account_ids:
                    rec.account_ids = [(6,0,account_ids.ids)]
    
    @api.onchange('company_id')  
    def onchange_company_id(self):
        for rec in self:
            list1=[(5,0,0)] 
            for child in rec.company_id.child_ids:
                list1.append(child)                       
            rec.child_company_ids=[(6,0,rec.company_id.child_ids.ids)]  
            
              
    def load_data(self):
        for rec in self:
            rec.partner_ids = False
            domain = [('parent_state', '=', 'posted')]
            # if self.env.user.has_group('account.group_account_manager'):
            #     if rec.child_company_ids:
            #         domain.append('|')
            #         domain.append(('company_id','=',rec.company_id.id))
            #         domain.append(('company_id','in',rec.child_company_ids.ids))
            #     else:
            #         domain.append(('company_id','=',rec.company_id.id))
            # else:
            #     domain.append(('company_id','=',rec.company_id.id))	
            company_ids = self.env.context.get('allowed_company_ids',[])
            if self.env.user.has_group('account.group_account_manager'):
                if company_ids:
                    # domain.append('|')
                    domain.append(('company_id','in',company_ids))
                else:
                    domain.append(('company_id','=',rec.company_id.id))
            else:
                domain.append(('company_id','=',rec.company_id.id))   
            if rec.account_ids:
                domain.append(('account_id','in',rec.account_ids.ids))
                
            if rec.partner_category_ids:
                domain.append(('partner_id.category_id', 'in', rec.partner_category_ids.ids))
                
            partner_ids = set(self.env['account.move.line'].search(domain).mapped('partner_id'))
            partner_ids = {partner for partner in partner_ids if not partner.ref_company_ids}
            
            line_ids = self.env['account.move.line'].search(domain,order='date asc,id asc')
            line_list = []
            from_0to30 = 0
            from_31to60 = 0
            from_61to90 = 0
            from_91to180 = 0
            
            from_0to45 =0
            from_46to90 =0
            from_91to180 =0
            from_181to365 =0
            from_366 =0
            # if self.amount == 'balance':
            for partner in partner_ids:
                if self.age_type == 'age_30':
                    from_0to30 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=30)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_31to60 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=31)),('date','>=',rec.date_as_on- timedelta(days=60)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_61to90= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=61)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_91to180= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_181to365= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_366= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    total = from_0to30 + from_31to60 + from_61to90 + from_91to180 + from_181to365 + from_366
                    
                     
                    lines0_30 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=30)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines31_60 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=31)),('date','>=',rec.date_as_on- timedelta(days=60)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_61_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=61)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_181_360 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    if from_0to30 != 0 or from_31to60 != 0 or from_61to90 != 0 or from_91to180 != 0 or from_181to365 != 0 or from_366 != 0:
                        vals = {
                                    'partner_id': partner.id,
                                    'days_0_30': from_0to30,
                                    'days_31_60': from_31to60,
                                    'days_61_90': from_61to90,
                                    'days_91_180' : from_91to180,
                                    'days_181_365' : from_181to365,
                                    'days_366_plus' : from_366,
                                    'total': total,
                                    }
                        line_list.append((0, 0, vals))
                        
                    line_list = sorted(line_list, key=lambda x: self.env['res.partner'].browse(x[2]['partner_id']).display_name)
                elif self.age_type == 'age_45':
                    
                    from_0to45 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=45)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_46to90 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=46)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_91to180= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_181to360= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_366= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    total = from_0to45 + from_46to90 + from_91to180 + from_181to360 + from_366
                    
                    lines_0_45 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=45)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_46_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=46)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_181_365 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    
                    if from_0to45 != 0 or from_46to90 != 0 or from_91to180 != 0 or from_181to360 != 0 or from_366 != 0:
                        vals = {
                                    'partner_id': partner.id,
                                    'days_0_45': from_0to45,
                                    'days_46_90': from_46to90,
                                    'dayss_91_180': from_91to180,
                                    'dayss_181_365' : from_181to360,
                                    'dayss_366_plus' : from_366,
                                    'total': total,
                                    }
                        line_list.append((0, 0, vals))
                    line_list = sorted(line_list, key=lambda x: self.env['res.partner'].browse(x[2]['partner_id']).display_name)
                    
                elif self.age_type == 'yearly':
                    
                    from_month_0_6 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=180)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_month_06_12 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_month_12_24= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('date','>=',rec.date_as_on- timedelta(days=731)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_month_24_36= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=732)),('date','>=',rec.date_as_on- timedelta(days=1097)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    from_month_366= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=1098)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
                    total = from_month_0_6 + from_month_06_12 + from_month_12_24 + from_month_24_36 + from_month_366
                    
                    lines_0_45 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=45)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_46_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=46)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_181_365 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                    
                    if from_month_0_6 != 0 or from_month_06_12 != 0 or from_month_12_24 != 0 or from_month_24_36 != 0 or from_month_366 != 0:
                        vals = {
                                    'partner_id': partner.id,
                                    'month_0_6': from_month_0_6,
                                    'month_6_12': from_month_06_12,
                                    'month_12_24': from_month_12_24,
                                    'month_24_36' : from_month_24_36,
                                    'month_36_plus' : from_month_366,
                                    'total': total,
                                    }
                        line_list.append((0, 0, vals))
                    line_list = sorted(line_list, key=lambda x: self.env['res.partner'].browse(x[2]['partner_id']).display_name)
            rec.partner_ids = line_list
                
                
            # else:
            #     for partner in partner_ids:
            #         if self.age_type == 'age_30':
            #             from_0to30 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=30)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_31to60 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=31)),('date','>=',rec.date_as_on- timedelta(days=60)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_61to90= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=61)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_91to180= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_181to365= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_366= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             total = from_0to30 + from_31to60 + from_61to90 + from_91to180 + from_181to365 + from_366
            #
            #
            #             lines0_30 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=30)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines31_60 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=31)),('date','>=',rec.date_as_on- timedelta(days=60)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_61_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=61)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_181_360 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #
            #
            #             if from_0to30 != 0 and from_31to60 != 0 and from_61to90 != 0 and from_91to180 != 0 and from_181to365 != 0 and from_366 != 0:
            #                 vals = {
            #                             'partner_id': partner.id,
            #                             'days_0_30': from_0to30,
            #                             'days_31_60': from_31to60,
            #                             'days_61_90': from_61to90,
            #                             'days_91_180' : from_91to180,
            #                             'days_181_365' : from_181to365,
            #                             'days_366_plus' : from_366,
            #                             'total': total,
            #                             }
            #                 line_list.append((0, 0, vals))
            #
            #             line_list = sorted(line_list, key=lambda x: self.env['res.partner'].browse(x[2]['partner_id']).display_name)
            #
            #
            #         elif self.age_type == 'age_45':
            #
            #             from_0to45 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=45)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_46to90 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=46)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_91to180= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_181to360= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_366= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             total = from_0to45 + from_46to90 + from_91to180 + from_181to360 + from_366
            #
            #             lines_0_45 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=45)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_46_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=46)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_181_365 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #
            #             if from_0to45 != 0 and from_46to90 != 0 and from_91to180 != 0 and from_181to360 != 0 and from_366 != 0:
            #                 vals = {
            #                             'partner_id': partner.id,
            #                             'days_0_45': from_0to45,
            #                             'days_46_90': from_46to90,
            #                             'dayss_91_180': from_91to180,
            #                             'dayss_181_365' : from_181to360,
            #                             'dayss_366_plus' : from_366,
            #                             'total': total,
            #                             }
            #                 line_list.append((0, 0, vals))
            #             line_list = sorted(line_list, key=lambda x: self.env['res.partner'].browse(x[2]['partner_id']).display_name)
            #
            #         elif self.age_type == 'yearly':
            #
            #             from_month_0_6 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=180)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_month_06_12 = sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_month_12_24= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('date','>=',rec.date_as_on- timedelta(days=731)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_month_24_36= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=732)),('date','>=',rec.date_as_on- timedelta(days=1097)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             from_month_366= sum(self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=1098)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)]).mapped('balance'))
            #             total = from_month_0_6 + from_month_06_12 + from_month_12_24 + from_month_24_36 + from_month_366
            #
            #             lines_0_45 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=45)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_46_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=46)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_181_365 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #             lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
            #
            #             if from_month_0_6 != 0 and from_month_06_12 != 0 and from_month_12_24 != 0 and from_month_24_36 != 0 and from_month_366 != 0:
            #                 vals = {
            #                             'partner_id': partner.id,
            #                             'month_0_6': from_month_0_6,
            #                             'month_6_12': from_month_06_12,
            #                             'month_12_24': from_month_12_24,
            #                             'month_24_36' : from_month_24_36,
            #                             'month_36_plus' : from_month_366,
            #                             'total': total,
            #                             }
            #                 line_list.append((0, 0, vals))
            #             line_list = sorted(line_list, key=lambda x: self.env['res.partner'].browse(x[2]['partner_id']).display_name)
            #     rec.partner_ids = line_list
    #
    #
    # summary = obj.dispatch_report_summary(obj.partner_id, obj.date)
    #         for line in summary:
    #             settled_till = line.calculate_settled_till_data(obj.date)
    #             balance = line.amount_currency - settled_till
    #
    #             if balance != 0:
            
        
    def partner_ageing_pdf(self):
       return self.env.ref('zb_financial_reports.action_partner_ageing_report').report_action(self)    
        
        
    def print_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        format_title1 = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
            'border': False
        })           
        format_title2 = workbook.add_format({
            'bold': False,
            'align': 'center',
            'font_size':10,
            'font': 'Times New Roman',
            'border': False
        })
        format_title3 = workbook.add_format({
            'bold': False,
            'align': 'center',
            'font_size':12,
            'font': 'Times New Roman',
            'border': False
        })
        format_title_head = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size':18,
            'font': 'Times New Roman',
            'border': False,          
        })
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
                                                                   'bold': True, 'size': 20,
                                                                   'font_name': 'Times New Roman',
                                                                   'color': 'black',
                                                                   'border': False,
                                                                   'text_wrap': False, 'shrink': True}),
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
                                                                      'text_wrap': False}),
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
        row=0
        col=0
        sheet = workbook.add_worksheet('Ageing Report')  
        
        
        sheet.set_column('A:A',35)
        sheet.set_row(0, 30)
        sheet.set_column('B:H',15)
        sheet.merge_range('C1:E1', 'Ageing Report', design_formats['heading_format_2'])
        # sheet.write(row,col+3,'Ageing Report',design_formats['heading_format_2'] )     
        row=row+1
        sheet.write(row+1,col,'Date As On : ',design_formats['heading_format_1'])
        sheet.write(row+2,col,'Partner Type : ',design_formats['heading_format_1'] )
        sheet.write(row+3,col,'Based On : ',design_formats['heading_format_1'] )        
        sheet.write(row+4,col,'Company : ',design_formats['heading_format_1'] )
        sheet.write(row+5,col,'Account(s) : ',design_formats['heading_format_1'] )
        sheet.write(row+6,col,'Age Type : ',design_formats['heading_format_1'] ) 
   
        sheet.write(row+1,col+1,self.date_as_on,design_formats['date_format'])
        sheet.write(row+2,col+1,str(self.partner_type if self.partner_type else ''),design_formats['normal_format_left'] )
        sheet.write(row+3,col+1,str(self.based_on),design_formats['normal_format_left'] )
        sheet.write(row+4,col+1,str(self.company_id.name),design_formats['normal_format_left'] )
        # child_list=[]
        
        accounts=''
        for account in self.account_ids:
            accounts += account.name+', '
        row=6
        sheet.write(row,col+1,accounts,design_formats['normal_format_left'] ) 
        sheet.write(row+1,col+1,str(self.age_type),design_formats['normal_format_left'] ) 
        
        
        # for company in self.child_company_ids:
        #     child_list.append(company.name)
            
        # row=8
        # sheet.write(row,col+2,'Child Companies ',format_title1 )
        # for company in child_list:
        #     sheet.write(row,col+3,str(company),format_title3 )
        #     row=row+1       
        row=row+4
        col=0
        
        sheet.write(row,col,'Partner',design_formats['heading_format_1'] )
        if self.age_type == 'age_30':
            sheet.write(row,col+1,'0-30D',design_formats['heading_format_3'] )
            sheet.write(row,col+2,'31-60D',design_formats['heading_format_3'] )
            sheet.write(row,col+3,'61-90D',design_formats['heading_format_3'] )
            sheet.write(row,col+4,'91-180D',design_formats['heading_format_3'] )
            sheet.write(row,col+5,'181-365 D',design_formats['heading_format_3'] )
            sheet.write(row,col+6,'366+ D',design_formats['heading_format_3'] )
            sheet.write(row,col+7,'Total',design_formats['heading_format_3'] )
            
        elif self.age_type == 'age_45':
            sheet.write(row,col+1,'0-45D',design_formats['heading_format_3'] )
            sheet.write(row,col+2,'46-90D',design_formats['heading_format_3'] )
            sheet.write(row,col+3,'91-180D',design_formats['heading_format_3'] )
            sheet.write(row,col+4,'181-365D',design_formats['heading_format_3'] )
            sheet.write(row,col+5,'366+ D',design_formats['heading_format_3'] )
            sheet.write(row,col+6,'Total',design_formats['heading_format_3'] )
            
        elif self.age_type == 'yearly':
            sheet.write(row,col+1,'6M',design_formats['heading_format_3'] )
            sheet.write(row,col+2,'6-12M',design_formats['heading_format_3'] )
            sheet.write(row,col+3,'12-24M',design_formats['heading_format_3'] )
            sheet.write(row,col+4,'24-36M',design_formats['heading_format_3'] )
            sheet.write(row,col+5,'36+ M',design_formats['heading_format_3'] )
            sheet.write(row,col+6,'Total',design_formats['heading_format_3'] )
            
        tot_from_0to30 = 0
        tot_from_31to60 = 0
        tot_from_61to90 = 0
        tot_from_91to180 = 0
        tot_from_181to365 = 0
        tot_from_366 = 0
        tot_total = 0
        
        tot_45_from_0to45 = 0
        tot_45_from_46to90 = 0
        tot_45_from_91to180 = 0
        tot_45_from_180to365 = 0
        tot_45_from_366 = 0
        tot_45_total = 0
        
        tot_from_0to6M = 0
        tot_from_6to12M = 0
        tot_from_12to24M = 0
        tot_from_24to36M = 0
        tot_from_36M = 0
        tot_m_total = 0
        
        
        for record in self.partner_ids:
            row=row+1
            sheet.write(row,col,str(record.partner_id.name),design_formats['normal_format_left'] )
            
            if self.age_type == 'age_30':
                sheet.write(row,col+1,str(round(record.days_0_30,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+2,str(round(record.days_31_60,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+3,str(round(record.days_61_90,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+4,str(round(record.days_91_180,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+5,str(round(record.days_181_365,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+6,str(round(record.days_366_plus,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+7,str(record.total),design_formats['normal_format_right'] )
            
                tot_from_0to30 += record.days_0_30
                tot_from_31to60 += record.days_31_60
                tot_from_61to90 += record.days_61_90
                tot_from_91to180 += record.days_91_180
                tot_from_181to365 += record.days_181_365
                tot_from_366 += record.days_366_plus
                
                tot_total += record.total
                
                sheet.write(row+1,col+1,str(round(tot_from_0to30,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+2,str(round(tot_from_31to60,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+3,str(round(tot_from_61to90,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+4,str(round(tot_from_91to180,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+5,str(round(tot_from_181to365,2)),design_formats['normal_format_right'])
                sheet.write(row+1,col+6,str(round(tot_from_366,2)),design_formats['normal_format_right'])
                
                
                sheet.write(row+1,col+7,str(round(tot_total,2)),design_formats['normal_format_right'])
                
            elif self.age_type == 'age_45':
                
                sheet.write(row,col+1,str(round(record.days_0_45,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+2,str(round(record.days_46_90,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+3,str(round(record.dayss_91_180,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+4,str(round(record.dayss_181_365,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+5,str(round(record.dayss_366_plus,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+6,str(record.total),design_formats['normal_format_right'] )
            
            
                tot_45_from_0to45 += record.days_0_45
                tot_45_from_46to90 += record.days_46_90
                tot_45_from_91to180 += record.dayss_91_180
                tot_45_from_180to365 += record.dayss_181_365
                tot_45_from_366 += record.dayss_366_plus
                
                tot_45_total += record.total
                
                sheet.write(row+1,col+1,str(round(tot_45_from_0to45,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+2,str(round(tot_45_from_46to90,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+3,str(round(tot_45_from_91to180,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+4,str(round(tot_45_from_180to365,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+5,str(round(tot_45_from_366,2)),design_formats['normal_format_right'])
                
                sheet.write(row+1,col+6,str(round(tot_45_total,2)),design_formats['normal_format_right'])
                
            elif self.age_type == 'yearly':
                
                sheet.write(row,col+1,str(round(record.month_0_6,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+2,str(round(record.month_6_12,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+3,str(round(record.month_12_24,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+4,str(round(record.month_24_36,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+5,str(round(record.month_36_plus,2)),design_formats['normal_format_right'] )
                sheet.write(row,col+6,str(record.total),design_formats['normal_format_right'] )
            
                tot_from_0to6M += record.month_0_6
                tot_from_6to12M += record.month_6_12
                tot_from_12to24M += record.month_12_24
                tot_from_24to36M += record.month_24_36
                tot_from_36M += record.month_36_plus
                
                tot_m_total += record.total
                
                sheet.write(row+1,col+1,str(round(tot_from_0to6M,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+2,str(round(tot_from_6to12M,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+3,str(round(tot_from_12to24M,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+4,str(round(tot_from_24to36M,2)),design_formats['normal_format_right'] )
                sheet.write(row+1,col+5,str(round(tot_from_36M,2)),design_formats['normal_format_right'])
                
                sheet.write(row+1,col+6,str(round(tot_m_total,2)),design_formats['normal_format_right'])
                
        
        workbook.close()
        output.seek(0)
        result = base64.b64encode(output.read())
        report_id = self.env['common.xlsx.out'].sudo().create({'filedata': result, 'filename': 'Ageing Report.xlsx'})

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=common.xlsx.out&field=filedata&id=%s&filename=%s.xlsx' % (
                report_id.id, 'Ageing Report'),
            'target': 'new',
        }
        output.close()
        
    def action_open_move_line(self,partner):
        
        lines = False
        for rec in self:
                lines0_30 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=30)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines31_60 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=31)),('date','>=',rec.date_as_on- timedelta(days=60)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_61_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=61)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_181_360 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                
                
                
                if self.env.context.get('days_0_30'):
                    lines = lines0_30
                elif self.env.context.get('days_31_60'):
                    lines = lines31_60
                elif self.env.context.get('days_61_90'):
                    lines = lines_61_90
                elif self.env.context.get('days_91_180'):
                    lines = lines_91_180
                elif self.env.context.get('days_181_365'):
                    lines = lines_181_360
                elif self.env.context.get('days_366_plus'):
                    lines = lines_366

        
        if lines:
            move_ids = lines.mapped('move_id').ids
            
            return {
            'name': _('Journal Entry'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', move_ids)],
            'target': 'current',
            'view_id': False,
            'views': False,
            'type': 'ir.actions.act_window'
        }
            
    def action_open_move_line_45_days(self,partner):
        lines = False
        for rec in self:
                lines_0_45 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=45)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_46_90 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=46)),('date','>=',rec.date_as_on- timedelta(days=90)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_91_180 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=91)),('date','>=',rec.date_as_on- timedelta(days=180)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_181_365 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_366 = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                
                
                
                if self.env.context.get('days_0_45'):
                    lines = lines_0_45
                elif self.env.context.get('days_46_90'):
                    lines = lines_46_90
                elif self.env.context.get('dayss_91_180'):
                    lines = lines_91_180
                elif self.env.context.get('dayss_181_365'):
                    lines = lines_181_365
                elif self.env.context.get('dayss_366_plus'):
                    lines = lines_366

        
        if lines:
            move_ids = lines.mapped('move_id').ids
            
            return {
            'name': _('Journal Entry'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', move_ids)],
            'target': 'current',
            'view_id': False,
            'views': False,
            'type': 'ir.actions.act_window'
        }
            
    def action_open_all_move_lines(self,partner):
        lines = False
        for rec in self:
                lines = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
        if lines:
            move_ids = lines.mapped('move_id').ids
            
            return {
            'name': _('Journal Entry'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', move_ids)],
            'target': 'current',
            'view_id': False,
            'views': False,
            'type': 'ir.actions.act_window'
        }
            
    def action_open_move_line_years(self,partner):
        lines = False
        
        for rec in self:
                lines_0_6_month = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','>=',rec.date_as_on- timedelta(days=180)),('date','<=',rec.date_as_on),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_6_12_month = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=181)),('date','>=',rec.date_as_on- timedelta(days=365)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_12_24_month = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=366)),('date','>=',rec.date_as_on- timedelta(days=731)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_24_36_month = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=732)),('date','>=',rec.date_as_on- timedelta(days=1097)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                lines_36_month = self.env['account.move.line'].search([('partner_id','=',partner.id),('date','<=',rec.date_as_on- timedelta(days=1098)),('parent_state','=','posted'),('account_id','in',rec.account_ids.ids)])
                
                
                
                if self.env.context.get('month_0_6'):
                    lines = lines_0_6_month
                elif self.env.context.get('month_6_12'):
                    lines = lines_6_12_month
                elif self.env.context.get('month_12_24'):
                    lines = lines_12_24_month
                elif self.env.context.get('month_24_36'):
                    lines = lines_24_36_month
                elif self.env.context.get('month_36_plus'):
                    lines = lines_36_month

        
        if lines:
            move_ids = lines.mapped('move_id').ids
            
            return {
            'name': _('Journal Entry'),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', move_ids)],
            'target': 'current',
            'view_id': False,
            'views': False,
            'type': 'ir.actions.act_window'
        }
        
class PartnerLines(models.TransientModel):
    _name="partner.lines"
    _description="Partner Lines"
           
    partner_lines_id=fields.Many2one("ageing.report.wizard")          
    partner_id=fields.Many2one("res.partner",string="Partner")
    days_0_30=fields.Float("0-30 Days")
    days_31_60=fields.Float("31-60 Days")
    days_61_90=fields.Float("61-90 Days")
    days_91_180=fields.Float("91-180 Days")
    days_181_365=fields.Float("181-365 Days")
    days_366_plus=fields.Float("366+ Days")
    
    days_0_45 = fields.Float("0-45 Days")
    days_46_90 = fields.Float("46-90 Days")
    dayss_91_180 = fields.Float("91-180 Days")
    dayss_181_365 = fields.Float("181-365 Days")
    dayss_366_plus = fields.Float("366+ Days")

    month_0_6= fields.Float("6 M")
    month_6_12 = fields.Float("6-12 M")
    month_12_24 = fields.Float("12-24 M")
    month_24_36 = fields.Float("24-36 M")
    month_36_plus = fields.Float("Above 36 M")
    
    total=fields.Float("Total")
    
    def action_open_move_line(self):
        res = self.partner_lines_id.action_open_move_line(self.partner_id)
        return res
    
    def action_open_move_line_45_days(self):
        res = self.partner_lines_id.action_open_move_line_45_days(self.partner_id)
        print("=========================================================lines",res)
        return res
    
    def action_open_move_line_years(self):
        res = self.partner_lines_id.action_open_move_line_years(self.partner_id)
        print("=========================================================lines",res)
        return res
    
    def action_open_all_move_lines(self):
        res = self.partner_lines_id.action_open_all_move_lines(self.partner_id)
        return res
    
         
    
    

    
    
    