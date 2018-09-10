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
import base64
import csv
import numpy as np
from openerp.exceptions import ValidationError
from datetime import datetime
from openerp import api, fields, models, _
from openerp.exceptions import UserError
import pytz


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


_logger = logging.getLogger(__name__)


class TrackSondaDelivery(models.Model):
    _name = 'tracksonda.delivery'
    _description = "Delivery"

    def _change_date_format(self, date):
        datetimeobject = datetime.strptime(date, '%d/%m/%Y')
        new_date = datetimeobject.strftime('%Y-%m-%d')
        return new_date

    name             = fields.Char(string=_("Ref.Envio"), required=True)
    date             = fields.Date(string="Fecha", required=True)
    horainicio       = fields.Datetime(string="Hora Inicio")
    horafin          = fields.Datetime(string="Hora Fin")
    carrier_id       = fields.Many2one("tracksonda.delivery.carrier", string=_("Transportista/Almacenista"), required=True )
    deliveryline_ids = fields.One2many('tracksonda.delivery.line','delivery_id')
    file             = fields.Binary(string="Archivo", help="File to check and/or import, raw binary (not base64)")
    company_id       = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env['res.company']._company_default_get('tracksonda'))
    state            = fields.Selection( [('draft', 'Borrador'),
                                        ('cancel', 'Cancelado'),
                                        ('run', 'Ejecutando'),
                                         ('done', 'Finalizado')
                                         ], 'Estado', readonly=True, track_visibility='onchange', copy=False, default='draft')

    @api.one
    def button_send_request(self):
        self.state= "run"
        self.horainicio=fields.Datetime.now()
        self.write({'state':self.state, 'horainicio':self.horainicio})


    @api.one
    def button_confirm_request(self):
        self.state="done"
        self.horafin = fields.Datetime.now()
        for reg in self.deliveryline_ids:
            if reg.date_incoming is None:
                raise ValidationError("No finaliza, faltan pedidos por entregar")

        self.write({'state': self.state, 'horafin': self.horafin})
        self.action_calculate_temp_cinetica()


    @api.one
    def button_cancel(self):
        self.state="draft"
        self.write({'state': self.state, 'horainicio': None,'horafin': None})

    @api.one
    def button_borrador(self):
        self.state = "cancel"
        self.write({'state': self.state, 'horafin': None})

    def str2float(self, amount, decimal_separator):
        if not amount:
            return 0.0
        try:
            if decimal_separator == '.':
                return float(amount.replace(',', ''))
            else:
                return float(amount.replace('.', '').replace(',', '.'))
        except:
            return False

    def str2int(self, amount, decimal_separator):
        if not amount:
            return 0
        try:
            if decimal_separator == '.':
                return int(amount.replace(',', ''))
            else:
                return int(amount.replace('.', '').replace(',', '.'))
        except:
            return False

    @api.one
    def action_button_import_csv(self):
        file = base64.decodestring(self.file)
        csv_iterator = csv.reader(StringIO(file), delimiter=";")

        iddelivery  = self.id
        if iddelivery:
            if self.state=="draft":
                for row in csv_iterator:

                    regloaddata = {'delivery_id': iddelivery,  'state':'P', 'nobultos': row[2], 'kilos': self.str2float(row[3],","), 'destinatario': row[4]
                                   , 'nopedido' : row[8], 'date' : self._change_date_format(row[1]), 'name' : row[0], 'cliente': row[10] }


                    self.deliveryline_ids.create(regloaddata)
            else:
                raise ValidationError("No se importa, cambie a  Borrador")
        else:
            raise ValidationError("No se importa, primero guarde...")

    @api.model
    def action_calculate_temp_cinetica(self):
        if self.state=="done":
            cr = self.env.cr
            TZ = pytz.timezone(self.env.user.tz)
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            DH     = 83.14472  # KJ/MOLE ENERGIA DE ACTIVACION
            GCR    = 8.314472  # KJ/MOLE/C CONSTANTE DE LOS GASES
            KELVIN = 273.15    # CERO ABSOULUTO
            diaspend = 0
            sql_2 = """select valor medtemp from tracksonda_loaddatson where  tiempo >=%s and tiempo <=%s and tracksonda_id = %s order by tiempo """

            tracksonda_ids = self.carrier_id.hub_id.tracksonda_ids

            entregas_ids = self.deliveryline_ids.sorted(lambda r: r.date_incoming )


            for reg in entregas_ids:
                #Corregir Timezone
                fechafin = pytz.utc.localize(datetime.strptime(reg.date_incoming,DATETIME_FORMAT)).astimezone(TZ)
                fechaini = pytz.utc.localize(datetime.strptime(self.horainicio,DATETIME_FORMAT)).astimezone(TZ)
                atc_med=[]
                for trc in tracksonda_ids: #Vehiculos con mas de un sensor
                    cr.execute(sql_2, (fechaini, fechafin, trc.id))
                    valores1 = cr.dictfetchall()
                    numero_datos = 0
                    denominador = 0
                    print valores1
                    for regval in valores1:
                        numero_datos = numero_datos + 1
                        temp = regval["medtemp"]
                        const = np.math.exp(-1 * DH / (GCR * (temp + KELVIN)))
                        denominador = const + denominador
                    if numero_datos != 0:
                        atc_med.append( ((DH / GCR) / (-1 * np.math.log(denominador / numero_datos))) - KELVIN)

                if len(atc_med)>0:
                    tc_med = reduce(lambda x,y: x+y, atc_med)/len(atc_med)
                    reg.write({'tempcinetica': tc_med })

    @api.one
    def write(self, vals):
        if self.state=='done':
            entregas_ids = self.deliveryline_ids.sorted(lambda r: r.date_incoming)
            fechainicial= None
            sw=0
            for reg in entregas_ids:
                if sw==0:
                    fechainicial= reg.delivery_id.horainicio
                    sw=1
                reg.write({'date_initial' : fechainicial})
                fechainicial = reg.date_incoming
        super(TrackSondaDelivery,self).write(vals)




class TracksondaDeliveryDetail(models.Model):
    _name = 'tracksonda.delivery.line'
    _description = "Delivery Lines"

    delivery_id   = fields.Many2one("tracksonda.delivery")
    date_initial  = fields.Datetime(string="F.Inicial")
    date_incoming = fields.Datetime(string="F.Entrega")
    date          = fields.Date(string="Fecha")
    state         = fields.Selection([('E', 'Entregado'), ('P', 'Pendiente'), ('D', 'Devuelto'),('A', 'Almacenable')], default="P")
    nobultos      = fields.Integer(string="No. Bultos")
    tempcinetica  = fields.Float(string="Temp.Cinetica")
    temperatura   = fields.Float(string="Temperatura")
    kilos         = fields.Float(string="Kilos")
    destinatario  = fields.Char(string="Destinatario")
    cliente       = fields.Char(string="Cliente")
    name          = fields.Char(string="Ref.Albaran")
    nopedido      = fields.Char(string="No. Pedido")



