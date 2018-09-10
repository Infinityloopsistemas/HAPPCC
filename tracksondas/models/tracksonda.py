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
import base64
from time import timezone
import os.path
import datetime
from pytz import timezone
import numpy as np
import plotly.plotly as py
from plotly.graph_objs import *
import colorsys
import random
from openerp.osv import osv
from openerp import api, fields, models, fields
from openerp import _, tools
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
from openerp.modules.module import get_module_resource, get_module_path
import logging

_logger = logging.getLogger('tracksondas.tracksonda')

OPCIONES_DIAS_1 = (
('S', _('Lunes a Sabado')), ('L', _('Lunes a Viernes')), ('F', _('Fin de Semana')), ('5', _('Sabado')),
('6', _('Domingo')), ('0', _('Lunes')), ('1', _('Martes')), ('2', _('Miercoles')), ('3', _('Jueves')),
('4', _('Viernes')))


def fechaEjecucion(fecha, diapro):
    """ Comprueba si s un  dia a agendizar
    :param fecha: dia a comprobar date
    :param diapro: parametrizacion del dia Integer
    :return: Boolean """
    print "---------------------------------------diapro %s " % diapro
    # OPCIONES_DIAS = ([('T',_('Ningun día')),('A',_('Todos los dias')),('L',_('Lunes a Viernes')),('F',_('Fin de Semana')),('5',_('Sabado')),('6',_('Domingo')),('0',_('Lunes')),('1',_('Martes')),('2',_('Miercoles')),('3',_('Jueves')),('4',_('Viernes'))])
    ndia = fecha.weekday()
    print "Dia ejecucion %s Dia programados %s " % (ndia, diapro)
    if diapro == 'T':
        # print "Entra en ningun dia"
        return False
    else:
        if ndia in (6, 5) and diapro == 'F':
            # print "Entra en Fines de semana"
            return True
        else:
            if diapro == 'A' or not diapro:
                # print "Entra en todos los dias"
                return True
            else:
                if ndia in (0, 1, 2, 3, 4) and diapro == 'L':
                    # print "Entra de lunes a viernes"
                    return True
                else:
                    if ndia in (0, 1, 2, 3, 4, 5) and diapro == 'S':
                        # print "Entra de lunes a sabado"
                        return True
                    else:
                        if str(ndia) == diapro:
                            # print "Entra en dia concreto %s" % ndia
                            return True
                        else:
                            # print "Ninguna opcion de las anteriores"
                            return False


class TrackSondaEnvios(models.Model):
    _name = "tracksonda.envios"
    _descripcion = "Envios de Graficas"
    _rec_name = "trackhub_id"
    # _inherit     = 'mail.message'

    active = fields.Boolean(string="Activo")
    tipo = fields.Selection(
        [('G', 'Genera Grafica'), ('A', 'Alerta Perdida Conexion'), ('C', 'Alerta fueras de Rango')])
    trackhub_id = fields.Many2one('tracksonda.hub')
    company_id = fields.Many2one('res.company', string="Local",
                                 default=lambda self: self.env['res.company']._company_default_get('tracksonda.envios'))
    partner_ids = fields.Many2many('res.partner', string='Destinatarios', domain=[('company_type', '=', 'person')])
    imagen = fields.Binary(string="Ultima Grafica", attachment=True)
    alarmas_ids = fields.One2many("tracksonda.alarmasson", "envios_id")
    tipoenvio = fields.Selection([('E', 'EMail'), ('S', 'SMS'), ('ES', ('Email/SMS'))])

    # ------------------------------------------------------
    # Template rendering
    # ------------------------------------------------------

    @api.multi
    def render_message(self, res_ids, template_id):
        self.ensure_one()
        multi_mode = True
        if isinstance(res_ids, (int, long)):
            multi_mode = False
            res_ids = [res_ids]

        model = 'tracksonda.envios'
        subjects = self.render_template("Graficas de Temperaturas", model, res_ids)
        bodies = self.render_template("Test", model, res_ids, post_process=True)
        emails_from = self.render_template("info@givasl.com", model, res_ids)
        replies_to = self.render_template("info@givasl.com", model, res_ids)

        default_recipients = self.env['mail.thread'].message_get_default_recipients(res_model=model, res_ids=res_ids)

        results = dict.fromkeys(res_ids, False)
        for res_id in res_ids:
            results[res_id] = {
                'subject': subjects[res_id],
                'body': bodies[res_id],
                'email_from': emails_from[res_id],
                'reply_to': replies_to[res_id],
            }
            results[res_id].update(default_recipients.get(res_id, dict()))

        # generate template-based values
        if template_id:
            template_values = self.generate_email_for_composer(
                template_id, res_ids,
                fields=['email_to', 'partner_to', 'email_cc', 'attachment_ids', 'mail_server_id'])
        else:
            template_values = {}

        for res_id in res_ids:
            if template_values.get(res_id):
                # recipients are managed by the template
                results[res_id].pop('partner_ids')
                results[res_id].pop('email_to')
                results[res_id].pop('email_cc')
                # remove attachments from template values as they should not be rendered
                template_values[res_id].pop('attachment_ids', None)
            else:
                template_values[res_id] = dict()
            # update template values by composer values
            template_values[res_id].update(results[res_id])

        return multi_mode and template_values or template_values[res_ids[0]]

    @api.model
    def generate_email_for_composer(self, template_id, res_ids, fields=None):
        """ Call email_template.generate_email(), get fields relevant for
            mail.compose.message, transform email_cc and email_to into partner_ids """
        multi_mode = True
        if isinstance(res_ids, (int, long)):
            multi_mode = False
            res_ids = [res_ids]

        if fields is None:
            fields = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to',
                      'attachment_ids', 'mail_server_id']
        # returned_fields = fields + ['partner_ids', 'attachments']
        returned_fields = fields + ['attachments']
        values = dict.fromkeys(res_ids, False)

        template_values = self.env['mail.template'].with_context(tpl_partners_only=True).browse(
            template_id).generate_email(res_ids, fields=fields)
        for res_id in res_ids:
            res_id_values = dict((field, template_values[res_id][field]) for field in returned_fields if
                                 template_values[res_id].get(field))
            res_id_values['body'] = res_id_values.pop('body_html', '')
            values[res_id] = res_id_values

        return multi_mode and values or values[res_ids[0]]

    @api.model
    def render_template(self, template, model, res_ids, post_process=False):
        return self.env['mail.template'].render_template(template, model, res_ids, post_process=post_process)

    @api.model
    @api.multi
    def cron_graph_temp(self):

        envios_regs = self.env['tracksonda.envios'].search([('active', '=', True), ('tipo', '=', 'G')])
        for objenvios in envios_regs:
            # print "Generando graficas por envios %s" % objenvios
            self.genera_grafica(objenvios)
            # self.genera_grafica_resumen(objenvios)
            email_obj = self.env['mail.template']
            template = email_obj.search([('name', '=', 'Grafica Temperatura')])
            email = email_obj.browse(template[0].id)
            attachment_ids = self.env['ir.attachment'].search(
                [('name', '=', 'imagen'), ('res_field', '=', 'imagen'), ('res_model', '=', objenvios._name),
                 ('res_id', '=', objenvios.id)])
            Mail = self.env['mail.mail']
            Mail = Mail.with_context(mail_notify_user_signature=False, mail_auto_delete=True,
                                     mail_server_id=email.mail_server_id.id)

            email_dir = ', '.join(map(lambda x: x, (str(partner.email) for partner in objenvios.partner_ids)))

            mail_values = {
                'subject': email.subject,
                'body': email.body_html or '',
                'email_to': email_dir,
                # 'parent_id': email.parent_id and email.parent_id.id,
                'partner_ids': [partner.id for partner in objenvios.partner_ids],
                'attachment_ids': [attach.id for attach in attachment_ids],
                # 'author_id': email.author_id.id,
                'email_from': email.email_from,
                'record_name': False,
                # 'no_auto_thread': email.no_auto_thread,
            }
            rendered_values = objenvios.render_message(1, template[0].id)
            email_dict = rendered_values
            mail_values['attachments'] = [(name, base64.b64decode(enc_cont)) for name, enc_cont in
                                          email_dict.pop('attachments', list())]
            attachment_ids = []

            for attach_id in mail_values.pop('attachment_ids'):
                new_attach_id = self.env['ir.attachment'].browse(attach_id).copy(
                    {'res_model': objenvios._name, 'res_id': objenvios.id, 'res_field': 'imagen'})
                attachment_ids.append(new_attach_id.id)

            mail_values['attachment_ids'] = self.env['mail.thread']._message_preprocess_attachments(
                mail_values.pop('attachments', []),
                attachment_ids, 'mail.message', 0)

            Mail.create(mail_values).send()
        return True

    def random_color(hue=None, sat=None, val=None):
        hue = hue / 360.0 if hue is not None else random.random()
        sat = sat if sat is not None else random.random()
        val = val if val is not None else random.random()
        to_eightbit = lambda value: int(round(value * 255))
        return map(to_eightbit, colorsys.hsv_to_rgb(hue, sat, val))

    @api.model
    @api.multi
    def genera_grafica(self, objenvios):
        """ Genera imagen de la grafica de los sensores """
        py.sign_in('', '')
        cr = self.env.cr
        fecha = (datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d'),
                                            '%Y-%m-%d') + datetime.timedelta(days=-1)).date()
        # fecha     = datetime.datetime(2016,4,10)
        objdatos = self.env['tracksonda.loaddatson']
        sql_family = """ select family as family from tracksonda  where hub_id=%s  group by  family """ % objenvios.trackhub_id.id
        cr.execute(sql_family)
        listfamilias = cr.dictfetchall()
        # Limpiamos attachment
        regobj = self.env['ir.attachment'].search(
            [('name', '=', 'imagen'), ('res_field', '=', 'imagen'), ('res_model', '=', objenvios._name),
             ('res_id', '=', objenvios.id)])
        for reg in regobj:
            reg.unlink()

        for familia in listfamilias:

            atrace = []
            annotations = []
            rowsensors = self.env['tracksonda'].search(
                [('hub_id', '=', objenvios.trackhub_id.id), ('family', '=', familia["family"])])

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
                           WHERE to_char(tiempo,'YYYY-mm-dd') =%s and tracksonda.id=%s
                        order by 2"""

                cr.execute(sql, (fecha.strftime("%Y-%m-%d"), sonda.id))
                regist = cr.dictfetchall()
                valores = []
                horas_x = []
                temperatura_y = []
                i = 0
                local_tz = timezone('Atlantic/Cape_Verde')

                for row in regist:
                    # horas_x.append(int(row['hora'][11:13]))
                    horas_x.append(
                        local_tz.localize(datetime.datetime.strptime(row['hora'], '%Y-%m-%d %H:%M'), is_dst=None))
                    temperatura_y.append(round(row['temp'], 2))
                    valores.append(
                        [local_tz.localize(datetime.datetime.strptime(row['hora'], '%Y-%m-%d %H:%M'), is_dst=None),
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

                    atrace.append(Scatter(
                        x=horas_x,
                        y=amedia_y,
                        line=dict(width=0.5),
                        name=" Media %s " % sonda.name,
                    ))

                    atrace.append(Scatter(
                        x=horas_x,
                        y=temperatura_y,
                        name=sonda.name,
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
                                    text="%s" % objenvios.trackhub_id.name,
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

            layout = dict(title='Grafica de Temperatura del dia %s de %s ' % (
            fecha.strftime("%Y-%m-%d"), objenvios.trackhub_id.company_id.name),
                          yaxis=dict(title='Temperatura (C)'),
                          xaxis=xaxis, width=1600, height=800
                          )
            layout['annotations'] = annotations

            nombfile = '%s_%s.png' % (objenvios.trackhub_id.macaddress.replace(":", "_"), familia["family"])

            image_save = get_module_path("tracksondas") + ("/static/img/%s" % nombfile)

            fig = Figure(data=atrace, layout=layout)

            py.image.save_as(fig, image_save)

            image_path = get_module_resource('tracksondas', 'static/img', nombfile)

            archivo = open(image_path, 'rb').read().encode('base64')
            # Guarda Imagen en Base de datos para enviar a posteriori
            attachment_data = {
                'name': 'imagen',
                'datas_fname': nombfile.strip(),
                'datas': archivo,
                'res_model': 'tracksonda.envios',
                'res_id': objenvios.id,
                'res_field': 'imagen',
                'file_size': len(archivo.encode('base64'))
            }

            idattach = self.env['ir.attachment'].create(attachment_data).id

    @api.model
    @api.multi
    def genera_grafica_resumen(self, objenvios):
        py.sign_in('jdarknet', 'jjy1dua07v')
        cr = self.env.cr
        fecha = (datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d'),
                                            '%Y-%m-%d') + datetime.timedelta(days=-240)).date()
        objdatos = self.env['tracksonda.loaddatson']
        sql_family = """ select family as family from tracksonda  where hub_id=%s  group by  family """ % objenvios.trackhub_id.id
        cr.execute(sql_family)
        listfamilias = cr.dictfetchall()
        # Limpiamos attachment
        regobj = self.env['ir.attachment'].search(
            [('name', '=', 'imagen'), ('res_field', '=', 'imagen'), ('res_model', '=', objenvios._name),
             ('res_id', '=', objenvios.id)])
        for reg in regobj:
            reg.unlink()

        for familia in listfamilias:
            atrace = []
            annotations = []
            rowsensors = self.env['tracksonda'].search(
                [('hub_id', '=', objenvios.trackhub_id.id), ('family', '=', familia["family"])])
            xy = []

            sql = """SELECT to_char(tiempo,'dd hh24') as hora,
                               avg(tracksonda_loaddatson.temperature) as temp
                              FROM tracksonda_loaddatson
                               INNER JOIN tracksonda ON
                                 tracksonda_loaddatson.tracksonda_id = tracksonda.id
                                INNER JOIN res_company ON
                               tracksonda.company_id = res_company.id
                                 WHERE to_char(tiempo,'YYYY-mm') =%s and tracksonda.hub_id=%s and tracksonda.family=%s
                                 group by to_char(tiempo,'dd hh24')
                              order by 1"""

            cr.execute(sql, (fecha.strftime("%Y-%m"), objenvios.trackhub_id.id, familia["family"]))
            regist = cr.dictfetchall()
            valores = []
            horas_y = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15",
                       "16", "17", "18", "19", "20", "21", "22", "23"]

            temperatura_z = []
            i = 0
            max_val = -30
            min_val = 30
            for row in regist:
                if i == 0:
                    pdia = str(row['hora'])[:2]
                    i = 1
                dia = str(row['hora'])[:2]

                if pdia == dia:

                    temperatura_z.append(round(row['temp'], 2))
                else:

                    valores.append(temperatura_z)
                    max_idx = np.amax(temperatura_z)
                    min_idx = np.amin(temperatura_z)

                    if max_idx > max_val:
                        max_val = max_idx
                    if min_idx < min_val:
                        min_val = min_idx
                    temperatura_z = []
                    pdia = str(row['hora'])[:2]

            dias_x = list(str(x).zfill(2) for x in range(1, len(valores), 1))
            trace1 = {
                "x": dias_x,
                "y": horas_y,
                "z": valores,
                "name": "TEMPERATURAS",
                "opacity": 1,
                "type": "heatmap",
                "zmax": max_val,
                "zmin": min_val,
                "zsmooth": "fast"
            }
            print trace1
            data = Data([trace1])
            layout = {
                "autosize": True,
                "bargap": 0.2,
                "bargroupgap": 0,
                "barmode": "stack",
                "boxgap": 0.3,
                "boxgroupgap": 0.3,
                "boxmode": "overlay",
                "dragmode": "zoom",
                "font": {
                    "color": "#000",
                    "family": "'Open sans', verdana, arial, sans-serif",
                    "size": 12
                },
                "height": 800,
                "hidesources": False,
                "hovermode": "x",
                "legend": {
                    "bgcolor": "#fff",
                    "bordercolor": "#000",
                    "borderwidth": 1,
                    "font": {
                        "color": "",
                        "family": "",
                        "size": 0
                    },
                    "traceorder": "normal"
                },
                "margin": {
                    "r": 200,
                    "t": 100,
                    "b": 80,
                    "l": 80,
                    "pad": 2
                },
                "paper_bgcolor": "#fff",
                "plot_bgcolor": "#fff",
                "separators": ".,",
                "showlegend": False,
                "title": "Promedio de temperaturas sondas durante el mes",
                "titlefont": {
                    "color": "",
                    "family": "",
                    "size": 0
                },
                "width": 1600,
                "xaxis": {
                    "anchor": "y",
                    "autorange": False,
                    "autotick": True,
                    "domain": [0, 32],
                    "dtick": 1,
                    "exponentformat": "e",
                    "gridcolor": "#ddd",
                    "gridwidth": 1,
                    "linecolor": "#000",
                    "linewidth": 1,
                    "mirror": "all",
                    "nticks": 0,
                    "overlaying": False,
                    "position": 0,
                    "range": [1, 31],
                    "rangemode": "normal",
                    "showexponent": "all",
                    "showgrid": True,
                    "showline": True,
                    "showticklabels": True,
                    "tick0": 0,
                    "tickangle": "auto",
                    "tickcolor": "#000",
                    "tickfont": {
                        "color": "",
                        "family": "",
                        "size": 0
                    },
                    "ticklen": 5,
                    "ticks": "outside",
                    "tickwidth": 1,
                    "title": "Dias",
                    "titlefont": {
                        "color": "",
                        "family": "",
                        "size": 0
                    },
                    "type": "category",
                    "zeroline": True,
                    "zerolinecolor": "#000",
                    "zerolinewidth": 1
                },
                "yaxis": {
                    "anchor": "x",
                    "autorange": False,
                    "autotick": True,
                    "domain": [-25, 30],
                    "dtick": 20,
                    "exponentformat": "e",
                    "gridcolor": "#ddd",
                    "gridwidth": 1,
                    "linecolor": "#000",
                    "linewidth": 1,
                    "mirror": "all",
                    "nticks": 0,
                    "overlaying": False,
                    "position": 0,
                    "range": [0, 23],
                    "rangemode": "normal",
                    "showexponent": "all",
                    "showgrid": True,
                    "showline": True,
                    "showticklabels": True,
                    "tick0": 0,
                    "tickangle": "auto",
                    "tickcolor": "#000",
                    "tickfont": {
                        "color": "",
                        "family": "",
                        "size": 0
                    },
                    "ticklen": 5,
                    "ticks": "outside",
                    "tickwidth": 1,
                    "title": "Horas",
                    "titlefont": {
                        "color": "",
                        "family": "",
                        "size": 0
                    },
                    "type": "linear",
                    "zeroline": True,
                    "zerolinecolor": "#000",
                    "zerolinewidth": 1
                }
            }
            fig = Figure(data=data, layout=layout)
            nombfile = 'res_%s_%s.png' % (objenvios.trackhub_id.macaddress.replace(":", "_"), familia["family"])

            image_save = get_module_path("tracksondas") + ("/static/img/%s" % nombfile)
            py.image.save_as(fig, image_save)

            image_path = get_module_resource('tracksondas', 'static/img', nombfile)

            archivo = open(image_path, 'rb').read().encode('base64')
            # Guarda Imagen en Base de datos para enviar a posteriori
            attachment_data = {
                'name': 'imagen',
                'datas_fname': nombfile.strip(),
                'datas': archivo,
                'res_model': 'tracksonda.envios',
                'res_id': objenvios.id,
                'res_field': 'imagen',
                'file_size': len(archivo.encode('base64'))
            }

            idattach = self.env['ir.attachment'].create(attachment_data).id

    @api.multi
    def _send_mail_avisos(self, model, template, email_dir, idenvio):
        res = False
        template_xmlid = template

        data_pool = self.env['ir.model.data']

        mail_pool = self.env['mail.mail']
        template_pool = self.env['mail.template']

        dummy, template_id = data_pool.get_object_reference(model, template_xmlid)
        email = template_pool.browse(template_id)
        email.email_to = email_dir
        mail_id = email.send_mail(idenvio, force_send=True)
        if mail_id:
            res = mail_pool.send([mail_id])
        return res

    @api.model
    @api.multi
    def cron_validate_periodic_write(self):
        """Verificamos que los registradores envian los datos a las sondas con la periodicidad configurada"""
        fmt = '%Y-%m-%d %H:%M:%S'
        cr = self.env.cr
        envios_regs = self.env['tracksonda.envios'].search([('active', '=', True), ('tipo', '=', 'A')])
        for obj_envios in envios_regs:
            obj_tracksonda = self.env['tracksonda'].search([('hub_id', '=', obj_envios.trackhub_id.id)])
            obj_avisoalarma = self.env["tracksonda.alarmasson"]
            sql_1 = """select to_char(max(tiempo), 'YYYY-MM-DD HH24:MI:SS') utiempo from tracksonda_loaddatson where tracksonda_id = %s  """
            tiempoactual = datetime.datetime.now()
            aobjid = []
            addenvios = []
            print "Tiempo Actual %s " % tiempoactual
            print "Objectos de Sondas %s" % obj_tracksonda

            for regtrack in obj_tracksonda:
                cr.execute((sql_1 % regtrack.id))
                registros = cr.dictfetchall()
                row = registros[0]
                if row['utiempo']:
                    tiempoultimo = datetime.datetime.strptime(row['utiempo'], fmt)
                else:
                    tiempoultimo = datetime.datetime.now()

                print "Tiempo ultimo %s " % tiempoultimo
                # Compara si deja de enviar en 5 periodos de aviso
                mincompara = int(regtrack.rangoaviso) * 5
                tiempocompara = tiempoactual + datetime.timedelta(minutes=-mincompara)
                print "Tiempo compara %s " % tiempocompara
                if tiempoultimo < tiempocompara:
                    objid = obj_avisoalarma.create(
                        {'envios_id': obj_envios.id, 'name': "Sin conexion: %s" % tiempocompara.strftime(fmt),
                         'dateaviso': tiempoactual.strftime(fmt), 'tracksonda_id': regtrack.id,
                         'company_id': obj_envios.company_id.id, 'fechaultimo': tiempoultimo.strftime(fmt),
                         'active': True})
                    aobjid.append(objid)

            print "Longitud  del objeto %s " % len(aobjid)
            if len(aobjid) != 0:
                if obj_envios.tipoenvio != 'S':
                    # Ubicamos solo destinatario de AVISOS EMAIL
                    email_dir = ', '.join(map(lambda x: x, (str(partner.email) for partner in
                                                            obj_envios.partner_ids)))
                    idmail = self._send_mail_avisos('tracksondas', 'email_template_data_recepcion', email_dir,
                                                    obj_envios.id)

                    # Actualizamos el envio
                    for obj_aviso in aobjid:
                        obj_aviso.write({'active': False})
                else:
                    smsmessages = self.env["textmagicsms.messages"]
                    for obj_aviso in aobjid:
                        texto = "%s dispositivo: %s" % (obj_aviso.name, obj_aviso.tracksonda_id.name)
                        for partner in obj_envios.partner_ids:
                            if partner.mobile:
                                smsmessages.create(
                                    {'name': partner.mobile, 'text': texto, 'model': "Alarma Sin Conexion"})
                        obj_aviso.write({'active': False})

        return True

    def _validarFecha(self, fecha, company_id):
        objfestivos = self.env['appcc.maestros.festivos']
        objexcepcio = self.env['appcc.excepcalendar']
        search_exec = [('company_id', '=', company_id), ('fechaini', '<=', fecha), ('fechafin', '>=', fecha)]
        search_fest = [('fechaini', '<=', fecha), ('fechafin', '>=', fecha),
                       ('name', 'in', ['FESTIVO NACIONAL', 'FESTIVO AUTONOMICO'])]
        numexcepcio = objexcepcio.search_count(search_exec)
        numfestloca = objfestivos.search_count(search_exec)
        numfestivos = objfestivos.search_count(search_fest)
        print "Fecha: %s Excepcion %s Festivo Local %s Festivos %s " % (fecha, numexcepcio, numfestloca, numfestivos)
        if not (numexcepcio == 0 and numfestloca == 0 and numfestivos == 0):
            return False
        else:
            return True

    @api.model
    @api.multi
    def cron_validate_range_out(self):
        """Verificamos que los datos de envio se encuentran dentro de los rangos que marcan los indicadores"""
        fmt = '%Y-%m-%d %H:%M:%S'
        print "Entra ..."
        cr = self.env.cr
        envios_regs = self.env['tracksonda.envios'].search([('active', '=', True), ('tipo', '=', 'C')])
        for obj_envios in envios_regs:
            obj_tracksonda = self.env['tracksonda'].search([('hub_id', '=', obj_envios.trackhub_id.id)])
            obj_avisoalarma = self.env["tracksonda.alarmasson"]
            obj_appccdetreg = self.env["appcc.detallesregistros"]
            # Conseguimos ultimo dato grabado obtenmos fecha y hora

            sql_1 = """select avg(valor) media,stddev(valor) stddes from tracksonda_loaddatson where tracksonda_id= %s and tiempo >
           (select max(tiempo)- interval '%s hours' utiempo from tracksonda_loaddatson where tracksonda_id= %s) """

            tiempoactual = datetime.datetime.now()

            aobjid = []
            addenvios = []
            for regtrack in obj_tracksonda:
                # Valor de histerisis de la consigna de avisos
                tolerancia = (regtrack.tolerancia / 100)
                # Tiempo para el calculo de estadistica
                tiemcalc = (regtrack.tmpocalc) or 2
                # Desviacion Estandar a comparar
                desstd = (regtrack.desstd) or 7
                hini = regtrack.hub_id.ihora
                hfin = regtrack.hub_id.fhora
                dias = regtrack.hub_id.dias
                b_aviso = False
                b_actaviso = fechaEjecucion(tiempoactual, dias)
                _logger.debug("HiO %s  HfO %s Hactual %s" % (hini, hfin, tiempoactual.hour))

                if not (hini <= tiempoactual.hour and hfin >= tiempoactual.hour) and b_actaviso:
                    _logger.debug('Entra en aviso en dias laborables fuera de horario')
                    b_aviso = True
                if not b_actaviso:
                    _logger.debug('Entra en aviso en dias no indicados')
                    b_aviso = True

                # Consulta las excepciones de calendario
                if not b_aviso:
                    b_aviso = not self._validarFecha(tiempoactual, regtrack.company_id.id)

                if b_aviso:
                    detreg = obj_appccdetreg.search([("tracksonda_id", "=", regtrack.id)])
                    vmax = detreg.indicador_id.vmax
                    vmin = detreg.indicador_id.vmin
                    _logger.debug(sql_1 % (regtrack.id, tiemcalc, regtrack.id))
                    cr.execute((sql_1 % (regtrack.id, tiemcalc, regtrack.id)))
                    registros = cr.dictfetchall()
                    row = registros[0]
                    valor = row['media']
                    desv = row['stddes']
                    _logger.debug("Valor: %s Desv: %s" % (valor, desv))
                    if vmax > 0:
                        cs = 1.0
                    else:
                        cs = -1.0
                    # Damos por bueno el datos siempre y cuando este en 7 desviaciones standar
                    _logger.debug("Consignas : Vmax %s , Vmin %s ,  Desv: %s" % (vmax, vmin, desstd))
                    _logger.debug("Logica %s" % (
                                not (valor < vmax * (1.0 + tolerancia * cs) and valor > vmin) and desv <= desstd))
                    _logger.debug("Operacion tolerancia  %s" % tolerancia)
                    if not (valor < vmax * (1.0 + tolerancia * cs) and valor > vmin) and desv <= desstd:
                        objid = obj_avisoalarma.create(
                            {'envios_id': obj_envios.id, 'name': "Limites de Control (%s,%s)" % (vmin, vmax),
                             'dateaviso': tiempoactual.strftime(fmt), 'tracksonda_id': regtrack.id,
                             'company_id': obj_envios.company_id.id, 'fechaultimo': tiempoactual.strftime(fmt),
                             'active': True, 'valor': valor})
                        aobjid.append(objid)

                print "Longitud  del objeto %s " % len(aobjid)
            if len(aobjid) != 0:
                # Ubicamos solo destinatario de AVISOS EMAIL
                email_dir = ', '.join(map(lambda x: x, (str(partner.email) for partner in
                                                        obj_envios.partner_ids)))

                idmail = self._send_mail_avisos('tracksondas', 'email_avisos_fuerarango', email_dir,
                                                obj_envios.id)
                # Actualizamos el envio
                for obj_aviso in aobjid:
                    obj_aviso.write({'active': False})

        return True


class TrackSondasHub(models.Model):
    _name = "tracksonda.hub"
    _descripcion = "Dispositivo concentrador de sondas "

    name = fields.Char(string="Hub", required=True)
    hostname = fields.Char(string="Host", required=True)
    macaddress = fields.Char(string="MAC Ethernet", required=True)
    ubicacion_id = fields.Many2one("res.partner", string="Ubicacion")
    fechaalta = fields.Date(string="Fecha Alta")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string="Empresa",
                                 default=lambda self: self.env['res.company']._company_default_get('tracksonda.hub'))
    tracksonda_ids = fields.One2many('tracksonda', 'hub_id')
    ihora = fields.Integer(string=_("Hora Oper inicio"), help=_("En formato 24 horas"))
    fhora = fields.Integer(string=_("Hora Oper fin"), help=_("En formato 24 horas"))
    dias = fields.Selection(OPCIONES_DIAS_1, string=_("Dias Trabajo"))
    tiporecepcion = fields.Selection([('P', 'HTTP'), ('F', 'ARCHIVO'), ('B', 'BASEDATOS')], default='P',
                                     string="Recepcion", help="Seleccionar el tipo de conexion")
    cadenaconexion = fields.Char(string="Cadena", help="Indicar la cadena de conexion al orige de los datos")

    @api.one
    @api.constrains('fhora', 'ihora')
    def _check_fhora(self):

        isOK = (self.fhora < 24 and self.fhora >= 0 and self.ihora < 24 and self.ihora >= 0)

        if isOK == False:
            raise ValidationError('El rango de hora tiene que estar entre 0 y 24')

        if self.fhora < self.ihora:
            raise ValidationError('La hora final no puede ser anterior a la hora inicial')

    def loadDirectoryData(self, objhub):
        import xmltodict
        import datetime
        import glob
        import os
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        tm_beginning = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, 0)
        tm = tm_beginning.strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.datetime.now()
        today_beginning = datetime.datetime(today.year, today.month, today.day, 0, 0, 0, 0)
        tb = today_beginning.strftime("%Y-%m-%d %H:%M:%S")
        if objhub.cadenaconexion:
            archivos = glob.glob("/home/ftpsiva/%s/*.xml" % objhub.cadenaconexion)
            # archivos = glob.glob("/vagrant/temp/*.xml")
            objdatadev = self.env['tracksonda.loaddatdev']

            for archivo in archivos:
                if archivo:
                    _logger.warning("Procesamos archivo ...........  ")
                    _logger.warning(archivo)
                    file = open(archivo, "r")
                    original_doc = file.read()
                    if len(original_doc) > 0:
                        try:
                            document = xmltodict.parse(original_doc)
                            base = document['file']['base']
                            serialbase = base['serial']
                            # objhub  = self.search([('hostname','=',serialbase)],limit=1)
                            hub_id = objhub.id
                            asondas = {}
                            for objsondas in objhub.tracksonda_ids:
                                asondas[objsondas.romid.strip()] = objsondas.id

                            itera = len(document['file']['group']['remote'])
                            registro = {}
                            grupo = document['file']['group']['name']
                            _logger.warning("IDS --- SONDAS")
                            _logger.warning(asondas)
                            for i in range(0, itera):
                                remote = document['file']['group']['remote'][i]
                                serial = str(remote['serial']).strip()
                                model = remote['model']
                                numcanal = remote['num']
                                humedad = 0
                                tempera = 0
                                valor1 = 0
                                iter2 = len(remote['ch'])
                                if int(iter2) == 2:
                                    for ii in range(0, int(iter2)):
                                        chanel = remote['ch'][ii]
                                        current = chanel['current']
                                        unixtime = current['unix_time']
                                        interval = chanel['record']['interval']
                                        data_id = chanel['record']['data_id']
                                        valido = current['value']['@valid']
                                        bateria = current['batt']
                                        unidad = current['unit']
                                        valor = current['value']['#text']
                                        if str(unidad) == "C":
                                            valor1 = current['value']['#text']
                                            tempera = float(valor1)
                                        if str(unidad) == "%":
                                            humedad = float(valor)
                                else:
                                    chanel = remote['ch']
                                    current = chanel['current']
                                    unixtime = current['unix_time']
                                    interval = chanel['record']['interval']
                                    data_id = chanel['record']['data_id']
                                    valor = current['value']['#text']
                                    valido = current['value']['@valid']
                                    bateria = current['batt']
                                    unidad = current['unit']
                                    valor = current['value']['#text']
                                    if str(unidad) == "C":
                                        try:
                                            tempera = float(valor)
                                        except ValueError:
                                            valido = "false"

                                    if str(unidad) == "%":
                                        try:
                                            humedad = float(valor)
                                        except ValueError:
                                            valido = "false"

                                existe = objdatadev.search(
                                    [('dataid', '=', data_id), ('hostname', '=', serial), ('hub_id', '=', hub_id),
                                     ('fechaalta', '>=', tb), ('fechaalta', '<', tm)], limit=1)
                                # existe = objdatadev.search([('dataid','=',data_id),('hostname','=', serial),('hub_id', '=' ,hub_id) ],limit=1)
                                _logger.warning("Parametros ... Estado: %s   Existe: %s  Data_id: %s  Serial: %s " % (
                                valido, existe, data_id, serial))
                                if len(existe) == 0 and valido == "true":
                                    tiempo = datetime.datetime.fromtimestamp(int(unixtime)).strftime(
                                        '%Y-%m-%d %H:%M:%S')
                                    regloaddev = {'dataid': data_id, 'hub_id': hub_id,
                                                  'fechaalta': fields.Datetime.from_string(tiempo),
                                                  'voltagepower': int(bateria), 'devicename': model, 'hostname': serial,
                                                  'devicesconnected': int(numcanal)}
                                    idloaddata = objdatadev.create(regloaddev)
                                    _logger.warning("Id creado %s " % idloaddata)
                                    regloaddata = {'loadatdev_id': idloaddata.id, 'tracksonda_id': asondas[serial],
                                                   'name': model, 'romid': serial, 'valor': tempera,
                                                   'temperature': tempera, 'humidity': humedad,
                                                   'tiempo': fields.Datetime.from_string(tiempo),
                                                   'company_id': objhub.company_id.id, 'intervalo': int(interval),
                                                   'channel': int(numcanal)}
                                    _logger.warning(regloaddata)
                                    self.env['tracksonda.loaddatson'].create(regloaddata)
                                else:
                                    if valido == "false":
                                        os.system('mv %s %s.err' % (archivo, archivo))
                                    else:
                                        file.close()
                                        os.system('rm -f %s' % archivo)
                        except xmltodict.expat.ExpatError:
                            os.system('mv %s %s.err' % (archivo, archivo))

                    file.close()

    @api.model
    @api.multi
    def cron_action_loaddata(self):
        for hub in self.env['tracksonda.hub'].search([('tiporecepcion', 'in', ['F', 'B'])]):
            if hub.tiporecepcion == 'F':
                self.loadDirectoryData(hub)
            if self.tiporecepcion == 'B':
                pass


class TrackSonda(models.Model):
    _name = "tracksonda"
    _descripcion = "Sondas a declarar"

    hub_id = fields.Many2one("tracksonda.hub", string="HUB", required=True)  # Dominio de la empresa por defecto
    name = fields.Char(string="Sonda", required=True)
    family = fields.Integer(string="Familia")
    romid = fields.Char(string="Identificador", required=True)
    rangoaviso = fields.Integer(string="T.Aviso (min)")
    tolerancia = fields.Float(string="Histerisis %", help="Valor que actua sobre el valor de consigna", default=10.0)
    tmpocalc = fields.Float(string="Per.Calc",
                            help="Periodo de tiempo para recopilar datos para el calculo de la desviacion standar y medias, menor mas sensible",
                            default=2)
    desstd = fields.Float(string="DSTD", default=7.0, help="Desviacion Standar")
    company_id = fields.Many2one('res.company', string="Empresa",
                                 default=lambda self: self.env['res.company']._company_default_get('tracksonda'))
    loaddatson_ids = fields.One2many("tracksonda.loaddatson", "tracksonda_id")
    active = fields.Boolean(default=True)


class LoadDataDev(models.Model):
    _name = "tracksonda.loaddatdev"
    _description = "Registros del estado del HUB y Sondas"

    hub_id = fields.Many2one("tracksonda.hub", string="HUB", required=True)
    fechaalta = fields.Datetime(string=("Fecha Alta"))
    company_id = fields.Many2one('res.company', string="Empresa",
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'tracksonda.loaddatdev'))
    pollcount = fields.Integer()
    devicesconnected = fields.Integer()
    looptime = fields.Float(digits=(10, 3))
    devicesconnectedchannel1 = fields.Integer()
    devicesconnectedchannel2 = fields.Integer()
    devicesconnectedchannel3 = fields.Integer()
    dataerrorschannel1 = fields.Integer()
    dataerrorschannel2 = fields.Integer()
    dataerrorschannel3 = fields.Integer()
    voltagechannel1 = fields.Float(digits=(10, 3))
    voltagechannel2 = fields.Float(digits=(10, 3))
    voltagechannel3 = fields.Float(digits=(10, 3))
    voltagepower = fields.Float(digits=(10, 3))
    devicename = fields.Char()
    hostname = fields.Char()
    macaddress = fields.Char()
    loaddatson_ids = fields.One2many("tracksonda.loaddatson", "loadatdev_id")
    dataid = fields.Char()  # lo utilizamos para los TandD

    @api.model
    def create(self, vals):
        vals['fechaalta'] = datetime.datetime.now()
        new_id = super(LoadDataDev, self).create(vals)
        return new_id


def fechaAlterada():
    return timezone.now() + datetime.timedelta(hours=1)


class LoadDatSon(models.Model):
    _name = "tracksonda.loaddatson"
    _description = "Registros de valores de las sondas"
    _order = "tiempo asc"

    def _convertirfecha(self):
        return self.tiempo.strftime('%Y-%m-%d')

    loadatdev_id = fields.Many2one("tracksonda.loaddatdev")
    tracksonda_id = fields.Many2one("tracksonda", string="Sonda")
    name = fields.Char(string="Modelo Sonda")
    family = fields.Integer()
    romid = fields.Char()
    health = fields.Integer()
    channel = fields.Integer()
    primaryvalue = fields.Char()
    valor = fields.Float(digits=(10, 3), group_operator="avg", string="Temp. C")
    temperature = fields.Float(digits=(10, 3), group_operator="avg", string="Temp. C")
    humidity = fields.Float(digits=(10, 3), group_operator="avg", string="Humedad Relativa %")
    dewpoint = fields.Float(digits=(10, 3), group_operator="avg", string="Pto. Rocio C")
    humidex = fields.Float(digits=(10, 3), group_operator="avg", string="Temp. Confort C")
    heatindex = fields.Float(digits=(10, 3), group_operator="avg", string="Sensacion Termica C")
    tiempo = fields.Datetime()
    company_id = fields.Many2one('res.company', string="Empresa")
    fecha = fields.Char(function=_convertirfecha, store=True, method=True)
    intervalo = fields.Integer("Intervalo lectura segundos")

    @api.model
    def create(self, vals):
        print vals
        vals['valor'] = vals['temperature']
        tiempo = vals.get('tiempo', False)
        if not tiempo:
            vals['tiempo'] = datetime.datetime.now()

        new_id = super(LoadDatSon, self).create(vals)
        return new_id


class TrackAlarmasSon(models.Model):
    _name = "tracksonda.alarmasson"
    _description = "Registros de Alarmas generadas por variacion de limites"

    name = fields.Char()
    tracksonda_id = fields.Many2one("tracksonda")
    envios_id = fields.Many2one("tracksonda.envios")
    dateaviso = fields.Datetime()
    valor = fields.Float(digits=(10, 3))
    active = fields.Boolean(default=True)
    fechaultimo = fields.Datetime()
    company_id = fields.Many2one('res.company', string="Empresa")
