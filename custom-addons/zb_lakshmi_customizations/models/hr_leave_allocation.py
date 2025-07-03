from odoo import models, fields, api
from datetime import timedelta


class HRLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"
    
    no_validity_days = fields.Integer(string="Validity Days", default=120, readonly=True)
    is_compensatory = fields.Boolean(string="Is Compensatory", compute="_compute_is_compensatory", store=True)
    
    @api.depends('holiday_status_id')
    def _compute_is_compensatory(self):
        for alloc in self:
            # Adjust this condition based on how compensatory leave is defined
            #alloc.is_compensatory = alloc.holiday_status_id.is_compensatory if alloc.holiday_status_id else False
            alloc.is_compensatory = alloc.holiday_status_id and alloc.holiday_status_id.name == "Compensatory Days"

    
    def action_approve(self):
        for alloc in self:
            if alloc.is_compensatory:
                base_date = alloc.date_from or fields.Date.today()
                alloc.date_to = base_date + timedelta(days=alloc.no_validity_days + 1)
        return super(HRLeaveAllocation, self).action_approve()
    
    def set_validity_days(self):
        for alloc in self:
            if alloc.state == 'validate' and alloc.no_validity_days >0:
               alloc.no_validity_days -= 1