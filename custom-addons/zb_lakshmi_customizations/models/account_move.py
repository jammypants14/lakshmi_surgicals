from odoo import models, fields,api


class AccountMove(models.Model):
    _inherit = "account.move"
    
    bank_details = fields.Html("Bank Details")
    pod_attached = fields.Boolean("POD Attached")
    product_vendor_ids = fields.Many2many(
        'res.partner',
        compute='_compute_vendor_ids',
        string='Vendors',
        store=True
    )
    pending_reason_id = fields.Many2one('pod.reason',string="Pending Reason")
    current_status =fields.Char(string="Current Status")
    last_action_update_date = fields.Datetime(string="Last Note Update On")
    next_action_update_date = fields.Date(string="Next Action Date")
    invoice_responsible_id = fields.Many2one('res.users',string="Responsible")


    @api.depends('invoice_line_ids.vendor_id')
    def _compute_vendor_ids(self):
        for order in self:
            vendors = order.invoice_line_ids.mapped('vendor_id')
            order.product_vendor_ids = vendors
    
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
    
    def update_vendor(self):
        for rec in self:
            if rec.invoice_line_ids:
               rec.invoice_line_ids._onchange_product_id_get_vendor()
            
    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        self.update_vendor()
        return res
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    vendor_id = fields.Many2one('res.partner', 'Vendor',)
    
    @api.onchange('product_id')
    def _onchange_product_id_get_vendor(self):
        for line in self:
            line.vendor_id = False
            product = line.product_id
            if product.seller_ids:
                vendor = product.seller_ids[0].partner_id
                line.vendor_id = vendor
    