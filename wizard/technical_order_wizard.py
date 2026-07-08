from odoo import models, fields

class TechnicalOrderRejectionWizard(models.TransientModel):
    _name = 'technical.order.reject.wizard'
    _description = 'Technical Order Rejection Wizard'

    rejection_reason = fields.Text(string='Reject Reason', required=True)

    def action_confirm(self):
        """Reject the technical order and save the rejection reason."""
        
        self.ensure_one()

        technical_order_id = self.env.context.get('active_id')
        technical_order = self.env['technical.order'].browse(technical_order_id)

        technical_order.write({
            'rejection_reason': self.rejection_reason,
            'state': 'rejected'
        })

        return {
            'type': 'ir.actions.act_window_close'
        }