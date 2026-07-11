from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
    sale_order_ids = fields.One2many('sale.order', 'technical_order_id', string="Sales Orders")
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=True)
    has_remaining_qty = fields.Boolean(compute='_compute_has_remaining_qty')
    sale_order_count = fields.Integer(string='Sales Orders', compute='_compute_order_count')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_be_approved', 'To Be Approved'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel'),

    ], default='draft', string="State")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """
           Validate that the end date is not earlier than the start date.
        """
        for rec in self:
            if rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(
                    _("End Date cannot be earlier than Start Date.")
                )

    @api.depends('order_line_ids.line_total')
    def _compute_total_price(self):
        """Compute the total amount of the technical order."""
        for order in self:
            order.total_price = sum(order.order_line_ids.mapped('line_total'))

    @api.depends('sale_order_ids')
    def _compute_order_count(self):
        """Compute the number of sales orders linked to each technical order."""
        for rec in self:
            rec.sale_order_count = self.env['sale.order'].search_count([
                ('technical_order_id', '=', rec.id),
            ])

    @api.depends('order_line_ids.quantity', 'sale_order_ids.state', 'sale_order_ids.order_line.product_uom_qty')
    def _compute_has_remaining_qty(self):
        """
        Compute whether the technical order still has remaining quantities
        that can be allocated to new confirmed sales orders.
        """
        for rec in self:

            rec.has_remaining_qty = False

            confirmed_sale_orders = rec.sale_order_ids.filtered(
                lambda so: so.state == 'sale'
            )

            confirmed_sale_lines = confirmed_sale_orders.mapped('order_line')

            for line in rec.order_line_ids:
                confirmed_qty = sum(
                    confirmed_sale_lines.filtered(
                        lambda sale_line: sale_line.product_id == line.product_id
                    ).mapped('product_uom_qty')
                )

                remaining_qty = line.quantity - confirmed_qty

                if remaining_qty > 0:
                    rec.has_remaining_qty = True
                    break


    @api.model
    def create(self, vals):
        """Generate sequence before creating a technical order."""

        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('technical.order')

        return super().create(vals)

    def action_to_be_approved(self):
        """Cancel the technical order."""

        self.write({'state': 'to_be_approved'})

    def action_cancel(self):
        """Cancel the technical order."""
        
        self.write({'state': 'cancel'})

    def action_approved(self):
        """
        Approve the technical order and notify all Sales Managers by email.
        """

        self.ensure_one()

        self.write({'state': 'approved'})

        group = self.env.ref('sales_team.group_sale_manager')

        for user in group.users:
            email = user.partner_id.email

            if not email:
                continue

            body_html = f"""
            <p>Hello {user.name},</p>

            <p>
                Technical Order <strong>{self.request_name}</strong> has been approved.
            </p>

            <p>
                <strong>Customer:</strong> {self.customer_id.name}<br/>
                <strong>Start Date:</strong> {self.start_date}<br/>
                <strong>End Date:</strong> {self.end_date}
            </p>

            <p>Regards,</p>
            """

            mail = self.env['mail.mail'].create({
                'email_to': email,
                'subject': f'Technical Order {self.request_name} Approved',
                'body_html': body_html,
            })

            mail.send()

    def action_draft(self):
        """Reset the technical order to the Draft state."""

        self.write({'state': 'draft'})

    def action_create_sale_order(self):
        """
        Create a draft sales order from the technical order.

        Only the remaining quantities (after confirmed sales orders)
        are copied into the new sales order.
        """

        self.ensure_one()

        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'technical_order_id': self.id,
        })

        confirmed_sale_orders = self.sale_order_ids.filtered(
            lambda so: so.state == 'sale'
        )

        confirmed_sale_lines = confirmed_sale_orders.mapped('order_line')

        for line in self.order_line_ids:

            confirmed_qty = sum(
                confirmed_sale_lines.filtered(
                    lambda sale_line: sale_line.product_id == line.product_id
                ).mapped('product_uom_qty')
            )

            remaining_qty = line.quantity - confirmed_qty

            if remaining_qty <= 0:
                continue

            self.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.display_name,
                'product_uom_qty': remaining_qty,
                'price_unit': line.price,
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
        }

    def action_view_sale_orders(self):
        """Open the sales orders related to the current technical order."""

        self.ensure_one()

        return {
            'name': _('Related Sales Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [
                ('technical_order_id', '=', self.id)
            ],
        }



class TechnicalOrderLine(models.Model):
    _name = 'technical.order.line'
    _description = 'Technical Order Line'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", default=1)
    price = fields.Float(string="Price")
    line_total = fields.Float(string="Total Price", compute="_compute_line_total", store=True)
    order_id = fields.Many2one('technical.order', string="Order", required=True, ondelete='cascade')

    @api.depends('quantity', 'price')
    def _compute_line_total(self):
        """Compute the total amount for each technical order line."""
        for line in self:
            line.line_total = line.quantity * line.price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update the line price when the selected product changes."""
        if self.product_id:
            self.price = self.product_id.list_price

    @api.constrains('quantity')
    def _check_quantity(self):
        """Ensure the quantity is greater than zero."""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(
                    _("Quantity must be greater than 0.")
                )