from odoo import models, fields, api


class TechnicalOrder(models.Model):
    _name = 'technical.order'
    _description = "Technical Order"

    sequence = fields.Char(string="Sequence", default="New", copy=False)
    request_name = fields.Char(string="Request Name", required=True)
    requested_by = fields.Many2one('res.users', string="Requested By",
                                   required=True, default=lambda self: self.env.user)
    customer_id = fields.Many2one('res.partner', string="Customer", required=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.today)
    end_date = fields.Date(string="End Date")
    rejection_reason = fields.Text(string="Rejection Reason")
    order_line_ids = fields.One2many('technical.order.line',
                                      'order_id', string="OrderLines")
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_be_approved', 'To Be Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel'),

    ], default='draft', string="State")

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('technical.order')

        return super().create(vals)

    def action_to_be_approved(self):
        self.write({
            'state': 'to_be_approved'
        })

    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })

    def action_approved(self):
        self.write({
            'state': 'approved'
        })


    def action_draft(self):
        self.write({
            'state': 'draft'
        })



class TechnicalOrderLine(models.Model):
    _name = 'technical.order.line'
    _description = 'Technical Order Line'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", default=1)
    price = fields.Float(string="Price")
    line_total =fields.Float(string="Total Price", compute="_compute_line_total", store=True)
    order_id = fields.Many2one('technical.order', string="Order", required=True, ondelete='cascade')