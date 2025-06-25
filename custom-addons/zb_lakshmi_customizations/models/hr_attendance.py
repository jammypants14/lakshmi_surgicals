from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, vals):
        self._check_duplicate_attendance(vals)
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            new_vals = vals.copy()
            new_vals.setdefault('employee_id', rec.employee_id.id)
            new_vals.setdefault('check_in', rec.check_in)
            new_vals.setdefault('check_out', rec.check_out)
            rec._check_duplicate_attendance(new_vals)
        return super().write(vals)

    def _check_duplicate_attendance(self, vals):
        employee_id = vals.get('employee_id')
        check_in = vals.get('check_in')
        check_out = vals.get('check_out')
       
        if not employee_id:
            return

        domain = [('employee_id', '=', employee_id)]

        if check_in:
            check_in_date = fields.Datetime.from_string(check_in).date()
            domain += [
                ('check_in', '>=', datetime.combine(check_in_date, datetime.min.time())),
                ('check_in', '<=', datetime.combine(check_in_date, datetime.max.time()))
            ]
        elif check_out:
            check_out_date = fields.Datetime.from_string(check_out).date()
            domain += [
                ('check_out', '>=', datetime.combine(check_out_date, datetime.min.time())),
                ('check_out', '<=', datetime.combine(check_out_date, datetime.max.time()))
            ]
        else:
            return

        # Exclude current record when writing
        if self.ids:
            domain.append(('id', 'not in', self.ids))

        existing = self.env['hr.attendance'].search(domain, limit=1)
        if existing:
            raise ValidationError(_("Multiple check-ins or check-outs are not allowed on the same day for this employee."))
