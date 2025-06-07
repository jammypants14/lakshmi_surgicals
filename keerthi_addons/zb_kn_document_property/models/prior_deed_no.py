from odoo import models, fields

class PriorDeedNo(models.Model):
    _name = 'prior.deed.no'
    _description = 'Prior Deed Number'

    name = fields.Char(string='Prior Deed No', required=True)
