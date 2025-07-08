from odoo import models, fields
from datetime import timedelta


class HRLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"
    
    no_validity_days = fields.Integer(string="Validity Days", default=120, readonly=True)
    
    def action_approve(self):
        for alloc in self:
            base_date = alloc.date_from or fields.Date.today()
            alloc.date_to = base_date + timedelta(days=121)
        return super(HRLeaveAllocation, self).action_approve()
    
    def set_validity_days(self):
        for alloc in self:
            if alloc.state == 'validate' and alloc.no_validity_days >0:
               alloc.no_validity_days -= 1