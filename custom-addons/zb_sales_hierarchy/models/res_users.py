from odoo import models, fields, api


class ResUsers(models.Model):
    
    _inherit = 'res.users'
    
    reporting_to_id = fields.Many2one('res.users',string="Reporting To")
    
