# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_


class ResPartner(models.Model):
    _inherit = "res.partner"
    
    
    def action_open_partner_ledger_report(self):
        """Trigger the Partner Ledger Report Wizard from a partner record."""
        
        wiz = self.env['partner.ledger.report.wiz'].create({
            'from_date': fields.Date.today(),
            'to_date': fields.Date.today(),
            #'account_type': 'receivable_payable',
            'partner_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner Ledger'),
            'res_model': 'partner.ledger.report.wiz',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wiz.id,
        }