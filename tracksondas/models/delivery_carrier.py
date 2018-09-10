# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 InfinityLoop Sistemas S.L (<http://www.infinityloop.es>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from openerp import api, fields, models, _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _name = 'tracksonda.delivery.carrier'
    _description = "Carrier delivery"

    name        = fields.Char(string="Transportista/Almacenista")
    type        = fields.Selection([('T','Transporte'),('A','Almacen')])
    hub_id      = fields.Many2one("tracksonda.hub", string="HUB", required=False, help="Sonda asociada al transporte/almacen para trazar temperatura controlada")
    partner_id  = fields.Many2one('res.partner', string='Transporter Company', required=True, help="The partner that is doing the delivery service.")
    country_ids = fields.Many2one('res.country',string='Paises')
    state_ids   = fields.Many2one('res.country.state',string='Estados')
    zip_from    = fields.Char('Zip From')
    zip_to      = fields.Char('Zip To')
    user_id     = fields.Many2one('res.users', string="Usuario SIVA", required=True)


