from odoo import models, fields,api


class AccountMove(models.Model):
    _inherit = "account.move"
    
    bank_details = fields.Html("Bank Details")
    
    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            company = self.env['res.company'].browse(vals['company_id'])
            if company.bank_details:
                vals['bank_details'] = company.bank_details
        else:
            # Use the default company if not explicitly passed
            company = self.env.company
            if company.bank_details:
                vals['bank_details'] = company.bank_details

        return super(AccountMove, self).create(vals)
    
    def action_update_bank_details(self):
        for rec in self:
            if rec.company_id:
                rec.bank_details=rec.company_id.bank_details