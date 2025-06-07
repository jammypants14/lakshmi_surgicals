from odoo import models, fields
class PriorDeedYear(models.Model):
    _name = 'prior.deed.year'
    _description = 'Prior Deed Year'

    name = fields.Char(string='Prior Deed Year', required=True)