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

import time
import datetime
from openerp import api, models
from openerp.modules.module import get_module_resource, get_module_path
from openerp import api, fields, models, _
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import dateutil
import pytz
from openerp.fields import Date





class DeliveryReport(models.AbstractModel):
    _name = 'report.tracksondas.tracksonda_report_delivery'


    def _horaZona(self,tiempo, fmt=None):
        TZ = pytz.timezone(self.env.user.tz)
        if fmt:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M"
        else:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        valor = pytz.utc.localize(datetime.datetime.strptime(tiempo, DATETIME_FORMAT)).astimezone(TZ).strftime(DATETIME_FORMAT)

        return valor

    @api.model
    @api.multi
    def _genera_grafica(self, objenvios, start, stop):

        color_sequence = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c',
                          '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5',
                          '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f',
                          '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']

        fig, ax = plt.subplots(1, 1, figsize=(21, 7))
        fig.subplots_adjust(left=.06, right=.90, bottom=.10, top=.90)
        fig.autofmt_xdate()
        # Formateo eje x
        xfmt = mdates.DateFormatter('%H:%m')
        ax.xaxis.set_major_locator(mdates.HourLocator())
        ax.xaxis.set_minor_locator(mdates.MinuteLocator())
        ax.xaxis.set_major_formatter(xfmt)
        # Eje y
        ax.yaxis.set_major_formatter(plt.FuncFormatter('{:.2f}C'.format))
        # Removemos lineas grafica
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(True)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()
        plt.grid(True, 'major', 'y', ls='--', lw=.5, c='k', alpha=.3)
        plt.grid(True, 'major', 'x', ls='--', lw=.3, c='k', alpha=.3)
        plt.tick_params(axis='both', which='both', bottom='off', top='off',
                        labelbottom='on', left='off', right='off', labelleft='on')
        plt.autoscale(enable=True,axis='x',tight=None)
        plt.xlabel('Tiempo')
        plt.ylabel('Temperatura')
        fig.suptitle('Monitorizacion temperatura  empresa:  %s' % objenvios.company_id.name, fontsize=14, ha='center')


        cr = self.env.cr
        fechafin = fields.Datetime.to_string(fields.Datetime.from_string(stop) + datetime.timedelta(minutes=30))
        fechaini = fields.Datetime.to_string(fields.Datetime.from_string(start) + datetime.timedelta(minutes=-30))
        objdatos = self.env['tracksonda.loaddatson']
        sql_family = """ select family as family from tracksonda  where hub_id=%s  group by  family """ % objenvios.id
        cr.execute(sql_family)
        listfamilias = cr.dictfetchall()

        for familia in listfamilias:

            atrace = []
            annotations = []
            rowsensors = self.env['tracksonda'].search(
                [('hub_id', '=', objenvios.id), ('family', '=', familia["family"])])
            i=0
            for sonda in rowsensors:
                xy = []
                # datos=objdatos.search([('tracksonda_id','=',sonda.id),('fecha','=',fecha.strftime("%Y-%m-%d"))])
                datos = objdatos.search([('tracksonda_id', '=', sonda.id)])

                sql = """SELECT tracksonda.name,
                                    to_char(tiempo,'yyyy-mm-dd hh24:mi') as hora,
                                     (tracksonda_loaddatson.temperature) as temp,
                                    res_company.name company
                                    FROM tracksonda_loaddatson
                                     INNER JOIN tracksonda ON
                                       tracksonda_loaddatson.tracksonda_id = tracksonda.id
                                      INNER JOIN res_company ON
                                     tracksonda.company_id = res_company.id
                                       WHERE to_char(tiempo,'yyyy-mm-dd hh24:mi') >=%s and to_char(tiempo,'yyyy-mm-dd hh24:mi') <=%s  and tracksonda.id=%s
                                    order by 2"""

                cr.execute(sql, (fechaini[:16], fechafin[:16], sonda.id))
                regist = cr.dictfetchall()
                valores = []
                horas_x = []
                temperatura_y = []
                i = 0
                pvarx = []
                pvary = []

                for row in regist:
                    # horas_x.append(int(row['hora'][11:13]))
                    horas_x.append(self._horaZona(row['hora'], "C"))
                    temperatura_y.append(round(row['temp'], 2))
                    valores.append(
                        [self._horaZona(row['hora'], "C"),
                         round(row['temp'], 2)])
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

                dhoras_x= [dateutil.parser.parse(s) for s in horas_x]
                print "Generando sonda %s" % sonda.name
                plt.plot(dhoras_x, temperatura_y,lw=1, color=color_sequence[i], label=sonda.name)
                i=+1
                plt.plot(dhoras_x, amedia_y, lw=1, color=color_sequence[i], label="Media %s " % sonda.name)
                i=+1

        normalizaname = objenvios.name.replace(" ", "_")
        image_save = get_module_path("appcc") + ("/static/img/%s.png" % normalizaname)
        image_path = get_module_resource('appcc', 'static/img', '%s.png' % normalizaname)
        leg = ax.legend(loc='upper right', bbox_to_anchor=(1, 1), shadow=True, ncol=1)
        leg.set_title("Sondas", prop={'size': 10})

        plt.savefig(image_save, bbox_inches='tight')
        if image_path:
                archivo = open(image_path, 'rb').read().encode('base64')
        else:
                archivo = None

        return archivo




    def _registros_temp(self, objhub, hinicio, hfin):
        # Zona UTC a  zona horaria del usuario
        res=[]
        regini=[]
        cr = self.env.cr
        TZ = self.env.user.tz
        fechafin = fields.Datetime.to_string(fields.Datetime.from_string(hfin) + datetime.timedelta(minutes=60))
        fechaini = fields.Datetime.to_string(fields.Datetime.from_string(hinicio) + datetime.timedelta(minutes=-60))

        print "------T--A--B--L---A----------"
        print "Fecha fin %s  -- Fecha ini %s " % (fechafin, fechaini)
        print " --------------------------------"

        objdatos = self.env['tracksonda.loaddatson']
        sql_family = """ select family as family from tracksonda  where hub_id=%s  group by  family """ % objhub.id
        cr.execute(sql_family)
        listfamilias = cr.dictfetchall()
        #Inicializamo columnas
        intervalos = ['7:00', '7:30', '8:00', '8:30', '9:00', '9:30', '10:00', '10:30', '11:00', '11:30',
                      '12:00', '12:30',
                      '13.00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
                      '18:00', '18:30', '19:00']
        _colcab = {}
        for colname_aux in intervalos:
            _colcab[colname_aux] = '-'

        for familia in listfamilias:
            atrace = []
            annotations = []
            reguni = {}
            rowsensors = self.env['tracksonda'].search(
                [('hub_id', '=', objhub.id), ('family', '=', familia["family"])])
            for sonda in rowsensors:
                xy = []
                datos = objdatos.search([('tracksonda_id', '=', sonda.id)])
                sql = """select series.minute as tiempo, coalesce(temp,0) as tempera ,to_char(series.minute + interval '60 minutes','hh24:mi')  as tiempo from
                (
                (SELECT to_timestamp(floor((extract('epoch' from tiempo AT TIME ZONE  %s) / 1800 )) * 1800) as interval_alias , avg(temperature) as temp
                   FROM tracksonda_loaddatson
                 INNER JOIN tracksonda ON
                   tracksonda_loaddatson.tracksonda_id = tracksonda.id
                  WHERE to_char(tiempo AT TIME ZONE  %s,'yyyy-mm-dd hh24:mi') >=%s and to_char(tiempo AT TIME ZONE  %s,'yyyy-mm-dd hh24:mi') <=%s and tracksonda.id=%s
                  group by interval_alias) promedio
                right join
                (SELECT generate_series(min(date_trunc('hour',tiempo AT TIME ZONE %s)),
                       max(date_trunc('minute',tiempo AT TIME ZONE %s )),'30m') as minute
                   FROM tracksonda_loaddatson
                 INNER JOIN tracksonda ON
                   tracksonda_loaddatson.tracksonda_id = tracksonda.id
                  WHERE to_char(tiempo AT TIME ZONE  %s,'yyyy-mm-dd hh24:mi') >=%s and to_char(tiempo AT TIME ZONE  %s,'yyyy-mm-dd hh24:mi') <=%s and tracksonda.id=%s) series
                  on series.minute=promedio.interval_alias
                ) order by 1"""


                cr.execute(sql, (TZ,TZ,fechaini[:16], TZ,fechafin[:16], sonda.id,TZ,TZ,TZ,fechaini[:16], TZ,fechafin[:16], sonda.id))
                regist = cr.dictfetchall()
                valores = []
                i = 0
                for row in regist:
                    valores.append({
                        'tiempo': row['tiempo'],
                        'tempe' : round(row['tempera'], 2)})

                #Transponemos el tiempo a columnas
                columna = _colcab.copy()
                for det in valores:
                    for colname in intervalos:
                        if det['tiempo'] == colname:
                            columna[det['tiempo']] = det['tempe']
                            break
                print "Sonda Nombre %s " % sonda['name']
                res.append({'sonda': sonda['name'], 'tabla': columna} )
                print res
        return res

    def _get_data_report(self, ids):
        objdelivery = self.env["tracksonda.delivery"]
        reid=[]
        for id in ids:
            regdeli = objdelivery.browse([id])
            cabecera={'name': regdeli.name, 'date': regdeli.date, 'carrier': regdeli.carrier_id.name,
                             'horainicio': self._horaZona(regdeli.horainicio)}

            entregas = []
            registros= []

            for detreg in regdeli.deliveryline_ids:
                entregas.append(
                    {'date_incoming': self._horaZona(detreg.date_incoming), 'cliente': detreg.cliente, 'tempcinetica': round(detreg.tempcinetica,2),
                     'kilos': detreg.kilos, 'destinatario': detreg.destinatario, 'name': detreg.name,
                     'nopedido': detreg.nopedido, 'nobultos': detreg.nobultos,
                     'date': regdeli.date,
                     'sondas': self._registros_temp(regdeli.carrier_id.hub_id, regdeli.horainicio, detreg.date_incoming)})

                grafica = self._genera_grafica(regdeli.carrier_id.hub_id, regdeli.horainicio, detreg.date_incoming)
                registros.append(  {'cab': cabecera ,'det': entregas, 'graf' : grafica })
                reid.append({'pagina' : registros })
                registros=[]
                entregas =[]

        return reid

    @api.multi
    def render_html(self, data=None):
        report = self.env['report']._get_report_from_name('tracksondas.tracksonda_report_delivery')
        registros_res = self._get_data_report(self._ids)
        intervalos = ['7:00', '7:30', '8:00', '8:30', '9:00', '9:30', '10:00', '10:30', '11:00', '11:30',
                      '12:00', '12:30',
                      '13.00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
                      '18:00', '18:30', '19:00']
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self.env[report.model].browse(self._ids),
            'deliverys': registros_res,
            'intervalos' : intervalos,
        }
        print docargs
        return self.env['report'].render('tracksondas.tracksonda_report_delivery', docargs)
