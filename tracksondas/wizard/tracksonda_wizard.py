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
from time import timezone
import datetime
import time
from openerp.osv import osv
from openerp import api, fields, models, fields
from openerp import _, tools
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
from openerp.modules.module import get_module_resource,get_module_path
import base64
import numpy as np
import plotly.plotly as py
from plotly.graph_objs import *
import plotly.tools as tls
import colorsys
import random
import pytz
import csv
import io
import itertools
import logging
import operator
import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO





class DataSonHorarioWizard(models.TransientModel):
    _name = "tracksonda.datsonwizard"
    _description ="Wizard de inicio calculo"

    tracksonda_ids  = fields.Many2many("tracksonda", string="Sonda",required=True)
    fecha           = fields.Date(required=False)
    tiempo_ini      = fields.Integer(string="Inicio",help="Colocar hora inicio",default=0)
    tiempo_fin      = fields.Integer(string="Fin",help="Colocar hora fin",default=24)
    data            = fields.Binary()

    @api.one
    @api.constrains("tiempo_ini","tiempo_fin")
    def _validarHoras(self):
        print "Entra %s %s " % (self.tiempo_ini,self.tiempo_fin)
        if self.tiempo_ini > self.tiempo_fin:
            raise ValidationError('La Hora inicial tiene que ser menor que la hora final')
        if self.tiempo_ini<0 or self.tiempo_fin>24:
            raise ValidationError('La Hora inicial tiene que estar en 0-23 horas')
        if self.tiempo_fin<0 or self.tiempo_fin>24:
            raise ValidationError('La Hora final tiene que estar en 0-23 horas')


    @api.multi
    def action_button_grafica_pdf(self):
        """ Genera imagen de la grafica de los sensores """
        #tls.set_credentials_file(username='jdarknet', api_key='jjy1dua07v')
        cr = self.env.cr
        fecha= self.fecha
        # fecha = (
        # datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d') + datetime.timedelta(
        #     days=-1)).date()
        # fecha     = datetime.datetime(2016,4,10)
        Attachment = self.env['ir.attachment']
        atrace = []
        annotations = []
        print "Fecha %s -------------" % fecha
        tiempo_ini = "%s %s:00:00" % (fecha, self.tiempo_ini)
        tiempo_fin = "%s %s:00:00" % (fecha, self.tiempo_fin)
        xy = []
            # datos=objdatos.search([('tracksonda_id','=',sonda.id),('fecha','=',fecha.strftime("%Y-%m-%d"))])

        for  tracks in self.tracksonda_ids:
            sql = """SELECT tracksonda.name,
                            to_char(tiempo,'yyyy-mm-dd hh24:mi') as hora,
                             (tracksonda_loaddatson.temperature) as temp,
                            res_company.name company
                            FROM tracksonda_loaddatson
                             INNER JOIN tracksonda ON
                               tracksonda_loaddatson.tracksonda_id = tracksonda.id
                              INNER JOIN res_company ON
                             tracksonda.company_id = res_company.id
                               WHERE tiempo>=to_timestamp('%s','yyyy-mm-dd hh24:mi') and tiempo <=to_timestamp('%s','yyyy-mm-dd hh24:mi') and tracksonda.id=%s
                            order by 2""" % (tiempo_ini,tiempo_fin, tracks.id)


            cr.execute(sql)
            regist = cr.dictfetchall()
            valores = []
            horas_x = []
            temperatura_y = []
            i = 0

            #local_tz= pytz.timezone(self.env.context['tz'])
            local_tz = pytz.timezone('Atlantic/Cape_Verde')
            for row in regist:
                # horas_x.append(int(row['hora'][11:13]))
                horas_x.append(local_tz.localize(datetime.datetime.strptime(row['hora'], '%Y-%m-%d %H:%M'),is_dst=None))
                temperatura_y.append(round(row['temp'], 2))
                valores.append([local_tz.localize(datetime.datetime.strptime(row['hora'], '%Y-%m-%d %H:%M'),is_dst=None), round(row['temp'], 2)])
                # valores.append([(row['hora']),round(row['temp'],2)])
                # valores.append([int(row['hora'][11:13]),round(row['temp'],2)])

            if len(valores) != 0:
                max_idx = np.argmax(temperatura_y)
                max_valy = temperatura_y[max_idx]
                max_valx = horas_x[max_idx]
                min_idx = np.argmin(temperatura_y)
                min_valy = temperatura_y[min_idx]
                min_valx = horas_x[min_idx]

                media_y = round(np.average(temperatura_y), 2)
                amedia_y = np.empty(len(horas_x))
                amedia_y.fill(media_y)

                atrace.append(Scatter(
                    x=horas_x,
                    y=amedia_y,
                    line=dict(width=0.5),
                    name=" Media %s " % tracks.name,
                ))

                atrace.append(Scatter(
                    x=horas_x,
                    y=temperatura_y,
                    name= tracks.name,
                ))

                annotations.append(dict(x=min_valx, y=min_valy,
                                        xanchor='right', yanchor='middle',
                                        text='Minimo {}'.format(min_valy) + "ºC",
                                        font=dict(family='Arial',
                                                  size=16,
                                                  color='rgb(182,128, 64)', ),
                                        showarrow=True, ))
                annotations.append(dict(x=max_valx, y=max_valy,
                                        xanchor='right', yanchor='middle',
                                        text='Maximo {}'.format(max_valy) + "ºC",
                                        font=dict(family='Arial',
                                                  size=16,
                                                  color='rgb(182,128, 64)', ),
                                        showarrow=True, ))

                annotations.append(dict(xref='paper', x=max_valx, y=media_y,
                                        xanchor='right', yanchor='middle',
                                        text='Media {}'.format(media_y) + "ºC",
                                        font=dict(family='Arial',
                                                  size=16,
                                                  color='rgb(182,128, 64)', ),
                                        showarrow=True, ))


            else:
                maxtemp = 0
                mintemp = 0

            annotations.append(dict(xref='paper', yref='paper', x=0, y=20,
                                    xanchor='center', yanchor='center',
                                    text="%s" % tracks.hub_id.name,
                                    font=dict(family='Arial',
                                              size=12,
                                              color='rgb(37,37,37)'),
                                    showarrow=False, ))

            xaxis = dict(
                title='Hora',
                showline=True,
                showgrid=True,
                showticklabels=True,
                nticks=24,
                linecolor='rgb(204, 204, 204)',
                linewidth=2,
                autotick=True,
                ticks='outside',
                tickcolor='rgb(204, 204, 204)',
                tickwidth=2,
                ticklen=5,
                tickfont=dict(
                    family='Arial',
                    size=12,
                    color='rgb(82, 82, 82)',
                ), )

            layout = dict(title='Grafica de Temperatura del dia %s  ' % fecha,
                          yaxis=dict(title='Temperatura (C)'),
                          xaxis=xaxis, width=1600, height=800
                          )
            layout['annotations'] = annotations




        nombfile = ('%s_%s.png' % (tracks.hub_id.macaddress, fecha)).replace(":", "_").replace("-","_")

        image_save = get_module_path("tracksondas") + ("/static/img/%s" % nombfile)

        py.sign_in('jdarknet', 'jjy1dua07v')

        fig = Figure(data=atrace, layout=layout)

        py.image.save_as(fig, image_save)

        image_path = get_module_resource('tracksondas', 'static/img', nombfile)

        archivo = open(image_path, 'rb').read().encode('base64')

        self.write({'data':archivo})


        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=tracksonda.datsonwizard&field=data&id=%s&filename=%s' % (self.id,nombfile),
            'target': 'self',
        }




    @api.multi
    def action_button_calchour(self):
        """Calculamos medias horarias durante la fecha señalada
        :param fecha:
        :return:
        """
        cr = self.env.cr
        obj_datsonhour=self.env['tracksonda.datsonhorario']
        tiempo_ini = "%s %s:00:00" % (self.fecha, self.tiempo_ini)
        tiempo_fin = "%s %s:00:00" % (self.fecha, self.tiempo_fin)

        asondas =[ sonda.id for sonda in self.tracksonda_ids ]

        if len(asondas) == 1:
            sondas ="(%s)" % asondas[0]
        else:
            sondas = tuple([ sonda.id for sonda in self.tracksonda_ids ])

        sql = """select tracksonda_id,date_part('hour',tiempo) hora, avg(valor) valor from tracksonda_loaddatson where  tracksonda_id in %s and tiempo>=to_timestamp('%s','yyyy-mm-dd hh24:mi') and tiempo <=to_timestamp('%s','yyyy-mm-dd hh24:mi')
                 group by  tracksonda_id,date_part('hour',tiempo) """ % (sondas,tiempo_ini,tiempo_fin)
        print sql
        cr.execute(sql)
        registros = cr.dictfetchall()
        print registros
        idtimeevent = str(time.mktime(datetime.datetime.now().timetuple()))
        for reg in registros:
            obj_datsonhour.create({'tracksonda_id': reg['tracksonda_id'], 'hora' : reg['hora'], 'valor': reg['valor'], 'fecha':self.fecha, 'idtimeevent': idtimeevent })

        ctx = dict()
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference('tracksondas', 'view_tracksonda_datsonhorario_graph')[1]
        except ValueError:
            compose_form_id = False


        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'tracksonda.datsonhorario',
            'views': [(compose_form_id, 'graph')],
            'view_id' : compose_form_id,
            'domain' : [('idtimeevent','=',idtimeevent)]
        }


class DataSonHorario(models.TransientModel):
    _name = "tracksonda.datsonhorario"
    _description ="Calculo de valores horarios"

    tracksonda_id   = fields.Many2one("tracksonda", string="Sonda")
    valor           = fields.Float(digits=(10,3), group_operator="avg")
    hora            = fields.Integer()
    fecha           = fields.Date()
    idtimeevent     = fields.Char()



FILE_TYPE_DICT = {
    'text/csv': ('csv', True, None),
}
EXTENSIONS = {
    '.' + ext: handler
    for mime, (ext, handler, req) in FILE_TYPE_DICT.iteritems()
}



class DataLoadFileCsv(models.TransientModel):
    _name = "tracksonda.datloadfilecsv"
    _description = "Subida de archivos csv a sondas"

    tracksonda_id = fields.Many2one("tracksonda", string="Sonda",required=True)
    date_ini      = fields.Date("Fecha de Inicio",required=True)
    date_end      = fields.Date("Fecha de Fin",required=True)
    file          = fields.Binary( string="Archivo", help="File to check and/or import, raw binary (not base64)",required=True)




    @api.one
    def action_button_import_csv(self):
        #Pendiente de normalizar la fecha y colocar el intervalo de fecha de importacion
        #de forma de no tener que fraccionar el archivo.
        file = base64.decodestring(self.file)
        csv_iterator = csv.reader(StringIO(file),delimiter=",")
        objdatadev = self.env['tracksonda.loaddatdev']

        for row in csv_iterator:
            print row[0]
            print row[1]
            print row[2]

            data_id  =row[1]
            tiempo   =datetime.datetime.strptime(str(row[0]),'%d/%m/%y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
            valor    =row[2]
            bateria  =5
            numcanal ="99"
            interval = 5
            serial = self.tracksonda_id.hub_id.name
            hub_id = self.tracksonda_id.hub_id.id
            model  = self.tracksonda_id.name
            regloaddev = {'dataid': data_id, 'hub_id': hub_id, 'fechaalta': fields.Datetime.from_string(tiempo),
                      'voltagepower': int(bateria), 'devicename': model, 'hostname': serial,'devicesconnected': int(numcanal)}

            idloaddata = objdatadev.create(regloaddev)
            regloaddata = {'loadatdev_id': idloaddata.id, 'tracksonda_id': self.tracksonda_id.id , 'name': model, 'romid': serial,
                       'valor': float(valor), 'temperature': float(valor),
                       'tiempo': fields.Datetime.from_string(tiempo), 'company_id': self.tracksonda_id.hub_id.company_id.id,
                       'intervalo': int(interval), 'channel': int(numcanal)}

            self.env['tracksonda.loaddatson'].create(regloaddata)




