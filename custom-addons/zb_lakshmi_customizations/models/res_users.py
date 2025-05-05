
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"
   
    company_seal = fields.Binary(string="Company Seal")
    signature = fields.Binary(string="Signature")


    
