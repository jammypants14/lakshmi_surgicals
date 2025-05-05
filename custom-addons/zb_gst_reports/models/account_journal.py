# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    
    gst_prefix_size  = fields.Integer(string="GST Prefix Size ")