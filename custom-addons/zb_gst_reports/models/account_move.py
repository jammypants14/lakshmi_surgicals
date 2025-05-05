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

from odoo.addons.l10n_in.models.account_invoice import AccountMove as l10n_invoice

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    gst_status = fields.Selection([
        ('not_uploaded', 'Not Uploaded'),
        ('ready_to_upload', 'Ready to upload'),
        ('uploaded', 'Uploaded to govt'),
        ('filed', 'Filed')
    ], "GST Status", default="not_uploaded", copy=False)
    invoice_type = fields.Selection([
        ('b2b', 'B2B'),
        ('b2cl', 'B2CL'),
        ('b2cs', 'B2CS'),
        ('b2bur', 'B2BUR'),
        ('import', 'IMPS/IMPG'),
        ('export', 'Export'),
        ('cdnr', 'CDNR')
    ], "Invoice Type", copy=False, tracking=True)

    l10n_in_company_country_code = fields.Char(related='company_id.country_id.code', string="Country code")
    
    prefix_sequence = fields.Char(string="Sequence Prefix For GST") 
    prefix_number = fields.Integer(string="Sequence Number For GST") 

    
    @api.onchange('partner_id')
    def onchange_partner_l10n_in_gstin(self):
        for rec in self:
            rec.l10n_in_gstin = rec.partner_id.vat

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.set_invoice_type()
        return res
    
    def action_set_invoice_type(self):
        for rec in self:
            out_inv = self.env['account.move'].search([('move_type', '=', 'out_refund'),('state','in',('posted','draft'))])
            
            for inv in out_inv:
                if inv.move_type == 'out_refund':
                    if inv.partner_id.country_id and inv.partner_id.country_id.id != inv.company_id.country_id.id:
                        inv.sudo().write({'invoice_type': 'export'})
                
    def set_invoice_type(self):
        for rec in self:
            if rec.move_type == 'out_invoice':
                if rec.partner_id.vat:
                    rec.invoice_type = 'b2b'
                else:
                    rec.invoice_type = 'b2cs'
                if rec.partner_id.country_id and rec.partner_id.country_id.id != rec.company_id.country_id.id:
                    rec.invoice_type = 'export'
            elif rec.move_type == 'out_refund':
                if rec.partner_id.country_id and rec.partner_id.country_id.id != rec.company_id.country_id.id:
                    rec.invoice_type = 'export'
                else:
                    rec.invoice_type = 'cdnr'
            
                
    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.set_invoice_type()
        for move in self:
	        if move.move_type in ('out_invoice', 'out_refund') and self.journal_id.gst_prefix_size and self.name:
	            prefix_sequence = move.name[:move.journal_id.gst_prefix_size]
	            prefix_number = move.name[move.journal_id.gst_prefix_size:]
	            
	            print("================prefix_sequence=======================",prefix_sequence)
	            print("================prefix_number=======================",prefix_number)
	            self.write({
	                'prefix_sequence': prefix_sequence,
	                'prefix_number': prefix_number,
	            })
        return res

    def _post(self, soft=True):
        """
        Overrides Post Method in l10n_in to removed GST Treatment checking
        """
        posted = super(l10n_invoice, self)._post(soft)
        for move in posted.filtered(lambda m: m.l10n_in_company_country_code == 'IN'):
            """Check state is set in company/sub-unit"""
            company_unit_partner = move.journal_id.company_id
            if not company_unit_partner.state_id:
                msg = """
                State is missing from your company/unit %(company_name)s (%(company_id)s).\n
                First set state in your company/unit.
                """
                raise ValidationError(_(
                    msg,
                    company_name=company_unit_partner.name,
                    company_id=company_unit_partner.id
                ))
            if self.journal_id.type == 'purchase':
                move.l10n_in_state_id = company_unit_partner.state_id
            shipping_partner = move.partner_shipping_id
            # move.l10n_in_gstin = self._l10n_in_get_shipping_partner_gstin(shipping_partner)
            if self.journal_id.type == 'sale':
                move.l10n_in_state_id = self._l10n_in_get_indian_state(shipping_partner)
                if not move.l10n_in_state_id:
                    move.l10n_in_state_id = self._l10n_in_get_indian_state(move.partner_id)
                if not move.l10n_in_state_id:
                    move.l10n_in_state_id = company_unit_partner.state_id
        return posted

    l10n_invoice._post = _post
    
    def action_update_prefix_sequence(self):
        if self._context.get('active_model') == 'account.move' and self._context.get('active_ids'):
            moves = self.env['account.move'].browse(self._context.get('active_ids')).filtered(lambda x: x.state in ('posted','cancel') and x.move_type in ('out_invoice', 'out_refund'))
            for move in moves: 
                if self.journal_id.gst_prefix_size > 0 and len(move.name) >= self.journal_id.gst_prefix_size:
                    prefix_sequence = move.name[:self.journal_id.gst_prefix_size]
                    prefix_number = move.name[self.journal_id.gst_prefix_size:]
                else:
                    prefix_sequence = move.name
                    prefix_number = ''
                move.prefix_sequence = prefix_sequence
                move.prefix_number = prefix_number
        return True

    @api.model
    def _l10n_in_get_indian_state(self, partner):
        """
        Override From l10n_in
        """
        if partner.country_id and partner.country_id.code == 'IN' and not partner.state_id:
            raise ValidationError(
                _("State is missing from address in '%s'. First set state after post this invoice again.",
                  partner.name))
        # elif partner.country_id and partner.country_id.code != 'IN':
        #     return self.env.ref('l10n_in.state_in_ot')
        return partner.state_id
