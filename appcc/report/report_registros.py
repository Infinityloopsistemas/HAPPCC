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

from datetime import datetime
from openerp import api, models
from openerp.modules.module import get_module_resource,get_module_path
import numpy as np
import plotly.plotly as py
import plotly.graph_objs as go

from openerp.fields import Date


class ReportRegistros_QR(models.AbstractModel):
    _name = 'report.appcc.report_detreg_qr'

    def _get_registros(self,detregids):
        registros_res =[]
        parimpar=0
        regultimo=False
        tmp1 = None
        tmp2 = None
        areg=[]
        for regid in detregids:
            i=0
            reguni             = {}
            cabreg             = self.env['appcc.detallesregistros'].browse([regid])
            if tmp1 is None:
                tmp1 =cabreg
            else:
                tmp2 =cabreg
            if ( cabreg.tpadquisicion !="M" and tmp1  and tmp2)  or regultimo :
                areg.append([{'lbl1': tmp1,'lbl2': tmp2}])
                tmp1=None
                tmp2=None

            if (regid == detregids[-1]) :
                regultimo=True
            if len(detregids)==1:
                areg.append([{'lbl1': tmp1, 'lbl2': tmp1}])


        reguni["cabecera"] = areg
        registros_res.append(reguni)
        print "---------------3------------ %s" %registros_res
        return registros_res


    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs       = self.env[self.model].browse(self.env.context.get('active_id'))
        detregids  = data['form']['detreg_id']
        registros_res   = self.with_context(data['form'].get('used_context',{}))._get_registros(detregids)
        docargs = {
            'doc_ids'  : self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'detregistros': registros_res
        }
        print "------------5------------- %s" % docargs
        return self.env['report'].render('appcc.report_detreg_qr', docargs)



class ReportRegistros(models.AbstractModel):
    _name = 'report.appcc.report_regfecha'

    def _get_registros(self,detregids,fecini,fecfin):

        registros_res =[]
        obj_firmas = self.env["appcc.registros.firmas"]


        for regid in detregids:
            i=0

            reguni ={}
            cabreg    = self.env['appcc.detallesregistros'].browse([regid])
            detreg    = self.env['appcc.registros'].search([('start_date','>=',fecini),('start_date','<=',fecfin),('detreg_id','=',regid)])
            areg =[]
            for reg in detreg:
                fecha   = reg.start_date
                idfirma = reg.firmas_id.id
                regemp  = None
                #print "Fecha %s y Firma %s " % (fecha,idfirma)

                firmareg = obj_firmas.search([('fecha_rel','=',fecha ),('firma_id','=',idfirma)],limit=1)
                if not firmareg:
                    regemp = reg.firmas_id

                areg.append([{"reg":reg , "regfir": firmareg, "regemp": regemp }])


            reguni["cabecera"] = cabreg
            reguni["detalle"]  = areg

            registros_res.append(reguni)
            #print "------------3------------- %s" % registros_res
        return registros_res


    def _get_datoslayout(self,detregids):

        registros_res =[]
        regid = detregids[0]
        objdetreg = self.env['appcc.detallesregistros'].browse([regid])
        registros_res.append({'revision_id': objdetreg.revision_id ,'company_id': objdetreg.company_id})

        #print "------------4------------- %s" % registros_res
        return registros_res


    @api.multi
    def render_html(self, data):

        self.model = self.env.context.get('active_model')
        docs       = self.env[self.model].browse(self.env.context.get('active_id'))

        fecini    = data['form'].get('date_from', True)
        fecfin    = data['form'].get('date_to', True)
        detregids = data['form']['detreg_id']
        registros_res   = self.with_context(data['form'].get('used_context',{}))._get_registros(detregids,fecini,fecfin)
        reg_datoslayout = self.with_context(data['form'].get('used_context',{}))._get_datoslayout(detregids)
        docargs = {
            'doc_ids'  : self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'registros': registros_res,
            'datoslayaout' : reg_datoslayout

        }
        print "------------5------------- %s" % docargs
        return self.env['report'].render('appcc.report_regfecha', docargs)



class ReportEvaluaRegistros(models.AbstractModel):
    _name = 'report.appcc.report_evalreg'

    def _get_registros(self,frecuencia_id,evallin_id,fecini,fecfin):

        if frecuencia_id:
            frec  = frecuencia_id[0]
        else :
            frec = None

        if evallin_id:
            evalid = evallin_id[0]
        else :
            evalid = None

        registros_res =[]
        i=0
        # for regid in detregids:
        reguni =[]
        regini ={}


        #print "----------EQUIPO---------- %s" % equip
        obj_evallin  = self.env['appcc.evaluacion.lineas'].search([('id','=',evalid),('fecha','>=',fecini),('fecha','<=',fecfin)], limit=1)
        #print "----------OBJ_EVALIN---------- %s" % obj_evallin


        #print "----------CABREG---------- %s" %obj_evallin.evaldet_id.regeval_id.id
        if frec:
            where=[('cabreg_id','=',obj_evallin.evaldet_id.regeval_id.id),('detreg_ids','!=',False),('frecuencia_id','=',frec)]
        else:
            where=[('cabreg_id','=',obj_evallin.evaldet_id.regeval_id.id),('detreg_ids','!=',False)]

        obj_detreg   = self.env['appcc.detallesregistros'].search(where)
        #print "----------ERROR---------- %s" % obj_detreg

        for detregs in obj_detreg:
            #print "Iterar %s" % detregs.id
            regobjs ={}
            obj_registro = self.env['appcc.registros'].search([('start_date','>=',fecini),('start_date','<=',fecfin),
                                                               ('detreg_id','=',detregs.id),('state','=','done')])
            regobjs          ={ "detgreg": detregs }
            regobjs["linreg"]= obj_registro
            reguni.append(regobjs)
            #print reguni

        regini ={"lineval" : obj_evallin}
        regini["detevalreg"] = reguni

        registros_res.append(regini)
        #print "------------3------------- %s" % registros_res

        return registros_res

    def _get_datoslayout(self,frecuencia_id,equipos_id):
        registros_res =[]
        equip_id = equipos_id[0]
        objdetreg = self.env['appcc.detallesregistros'].search([('equipos_id','=',equip_id)],limit=1)
        registros_res.append({'company_id': objdetreg.company_id})

        print "------------4------------- %s" % registros_res
        return registros_res


    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs       = self.env[self.model].browse(self.env.context.get('active_id'))

        fecini     = data['form'].get('date_from', True)
        fecfin     = data['form'].get('date_to', True)
        evallinid  = data['form']['evallin_id']
        equipid    = data['form']['equipo_id']
        frecuenid  = data['form']['frecuencia_id']
        registros_res   = self.with_context(data['form'].get('used_context',{}))._get_registros(frecuenid,evallinid,fecini,fecfin)
        reg_datoslayout = self.with_context(data['form'].get('used_context',{}))._get_datoslayout(frecuenid,equipid)
        docargs = {
            'doc_ids'  : self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'evaluaciones': registros_res,
            'datoslayaout' : reg_datoslayout

        }
        #print "------------5------------- %s" % docargs
        return self.env['report'].render('appcc.report_evalreg', docargs)

#Evaluaciones por empresas y por totales

class ReportTotEvalRes(models.AbstractModel):
    _name = 'report.appcc.report_toteval_res'


    def _get_indicador(self,start,stop,company_id):
        res = []
        sql = """
                        select tmp.id id, tmp.name indicador from appcc_template_evaluador tmp
                        join appcc_evaluacion_detalle det on (det.indicador_id= tmp.id)
                        join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                        join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                        where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                        and  eval.company_id=%s and det.puntua!=0
                        group by tmp.name,tmp.id
                    """ % (start, stop, company_id)
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()

    def _get_cabecera_col(self,start,stop,company_id):
        res=[]
        res.append({'name': 'EVALUAR'})
        sql ="""
                select det.name cabecera from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id=%s and det.puntua!=0
                group by det.name
                order by det.name
            """ % (start,stop,company_id)

        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['cabecera']})
        return res

    def _get_puntuacion(self,start,stop,company_id,indi_id):
        res=[]
        sql="""
                select det.name cabecera,avg(det.puntua) puntua from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id=%s and det.indicador_id=%s and det.puntua!=0
                group by det.name
                order by det.name
            """ % (start,stop,company_id,indi_id)
        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['cabecera'], 'puntua': round(row['puntua'],2) })
        return res

    def _get_total(self,start,stop,company_id):
        res=[]
        sql ="""
                select det.name cabecera, avg(det.puntua) totpunt from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id=%s and det.puntua!=0
                group by det.name
                order by det.name
            """ % (start,stop,company_id)
        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['cabecera'], 'total': round(row['totpunt'], 2)})
        return res


    def _get_registros(self,start,stop):
        registros_res =[]
        i=0
        reguni ={}
        regini =[]
        columna = []
        cabcol=[]
        busca =[]
        total = []
        totales ={}
        company_id = self.env['res.company']._company_default_get('appcc.evaluacion')
        obj_indicador = self._get_indicador(start,stop,company_id.id)
        #Revisamos para inicializar las cabeceras
        cabcol = self._get_cabecera_col(start,stop,company_id.id)
        total  = self._get_total(start,stop,company_id.id)
        #Normalizamos los totales por columnas
        for totcol in total:
            totales[totcol['name']]=totcol['total']

        for colname_aux in cabcol:
            busca.append(colname_aux['name'])
        _colcab={}
        for colname_aux in busca[1:]:
            _colcab[colname_aux] = '-'

        #Llenado de datos
        for indicador in obj_indicador:
            obj_evadet    = self._get_puntuacion(start,stop,company_id.id,indicador["id"])
            if len(obj_evadet)!=0:
                reguni = {"indicador": indicador['indicador']}
                columna = _colcab.copy()
                for det in obj_evadet:
                    for colname in busca[1:]:
                        if det['name']== colname:
                            columna[det['name']]  = det['puntua']
                            break

                reguni['evals']=columna
                regini.append(reguni)
                reguni = {}


        registros_res.append({ 'cabcol': cabcol, 'totevals' : regini, 'cabrow': cabcol[1:], 'total':totales, 'company_id': company_id, 'start': start,'stop':stop })
        #print "------------3------------- %s" % registros_res
        return registros_res

    def _get_datoslayout(self,start,stop):
        registros_res =[]
        #registros_res.append({'company_id': objeval.company_id})
        #objeval = self.env['appcc.evaluacion'].search([('id', '=', det.evallin_id.evaldet_id.id)], limit=1)
        #regini.append({'tecnico': objeval.tecnicos_id.name, 'local': objeval.company_id.name, 'fecha': objeval.fecha,
        #                       'name': objeval.name, 'totevals': reguni})

        #print "------------4------------- %s" % registros_res
        return registros_res


    @api.multi
    def render_html(self, data):
        print "Entra en el render .---------------------------------------------------"
        self.model = self.env.context.get('active_model')
        docs       = self.env[self.model].browse(self.env.context.get('active_id'))
        start = data['form']['used_context'].get('start')
        stop  = data['form']['used_context'].get('stop')

        registros_res   = self.with_context(data['form'].get('used_context',{}))._get_registros(start,stop)
        reg_datoslayout = self.with_context(data['form'].get('used_context',{}))._get_datoslayout(start,stop)
        docargs = {
            'doc_ids'  : self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'evaluaciones': registros_res,

            }
        print "------------5------------- %s" % docs
        print "------------6--------------%s" % self.model
        return self.env['report'].render('appcc.report_toteval_res', docargs)


#Resumen Evaluaciones Totales Grupo de Empresas

class ReportTotEvalMulti(models.AbstractModel):
    _name = 'report.appcc.report_toteval_multi'

    def genera_grafica(self, start,stop):
        """ Genera imagen de la grafica de los sensores """

        f_start = Date.from_string(start)
        f_stop  = Date.from_string(stop)
        delta   = f_stop-f_start
        if delta.days <=30:
            return False

        obj_company = self.env['res.company'].sudo()
        company_ids = self._get_companys()
        company_matriz = obj_company.search([('id', 'not in', company_ids.split(','))], limit=1)
        atrace = []
        annotations = []

        for company_id in company_ids.split(","):
            name_company = obj_company.browse([int(company_id)]).name

            xy = []
            regist = self._get_punt_company_mes(start,stop,int(company_id))
            valores = []
            mes_x = []
            puntua_y = []
            i = 0
            for row in regist:
                mes_x.append(row['mes'])
                puntua_y.append(round(row['puntua'], 2))
                valores.append([(row['mes']), round(row['puntua'], 2)])


            if len(valores) != 0:
                max_idx = np.argmax(puntua_y)
                max_valy = puntua_y[max_idx]
                max_valx = mes_x[max_idx]
                min_idx = np.argmin(puntua_y)
                min_valy = puntua_y[min_idx]
                min_valx = mes_x[min_idx]

                media_y = round(np.average(puntua_y), 2)
                amedia_y = np.empty(len(mes_x))
                amedia_y.fill(media_y)

                atrace.append(go.Scatter(
                    x=mes_x,
                    y=amedia_y,
                    line=dict(width=0.5),
                    name=" Media %s " % name_company,
                    ))

                atrace.append(go.Scatter(
                    x=mes_x,
                    y=puntua_y,
                    name=name_company,
                    ))

                annotations.append(dict(x=min_valx, y=min_valy,
                                        xanchor='right', yanchor='middle',
                                        text='Min {}'.format(min_valy),
                                        font=dict(family='Arial',
                                                  size=16,
                                                  color='rgb(182,128, 64)', ),
                                        showarrow=True, ))
                annotations.append(dict(x=max_valx, y=max_valy,
                                        xanchor='right', yanchor='middle',
                                        text='Max {}'.format(max_valy),
                                        font=dict(family='Arial',
                                                  size=16,
                                                  color='rgb(182,128, 64)', ),
                                        showarrow=True, ))

                annotations.append(dict(xref='paper', x=max_valx, y=media_y,
                                        xanchor='right', yanchor='middle',
                                        text='Media {}'.format(media_y) ,
                                        font=dict(family='Arial',
                                                  size=16,
                                                  color='rgb(182,128, 64)', ),
                                        showarrow=True, ))


            else:
                maxpunt = 0
                minpunt = 0

        annotations.append(dict(xref='paper', yref='paper', x=20, y=30,
                                xanchor='center', yanchor='center',
                                text="%s" % company_matriz.name,
                                font=dict(family='Arial',
                                          size=12,
                                          color='rgb(37,37,37)'),
                                showarrow=False, ))

        xaxis = dict(
            title='Meses',
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

        layout = dict(title='EVALUACIONES COMPRENDIDAS DESDE  %s HASTA %s ' % (start,stop),
                      yaxis=dict(title='Puntos'),
                      xaxis=xaxis, width=1600, height=1000
        )
        layout['annotations'] = annotations
        normalizaname = company_matriz.name.replace(" ","_")
        fig = go.Figure(data=atrace, layout=layout)
        py.sign_in('jdarknet', 'jjy1dua07v')
        image_save = get_module_path("appcc") + ("/static/img/%s.png" % normalizaname)
        image_path = get_module_resource('appcc', 'static/img','%s.png' % normalizaname)
        py.image.save_as(fig, image_save)
        i=0
        while i < 10:
            time.sleep(1)
            try:
                archivo = open(image_path, 'rb').read().encode('base64')
            except IOError:
                i=i+1
            else:
                i=i+1

        return archivo




    def _get_indicador(self,start,stop,company_ids):
        sql = """       select tmp.id id, tmp.name indicador from appcc_template_evaluador tmp
                        join appcc_evaluacion_detalle det on (det.indicador_id= tmp.id)
                        join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                        join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                        where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                        and  eval.company_id in (%s) and det.puntua!=0
                        group by tmp.name,tmp.id
                    """ % (start, stop, company_ids)
        self.env.cr.execute(sql)
        return self.env.cr.dictfetchall()

    def _get_cabecera_col(self,start,stop,company_ids):
        res=[]
        res.append({'name': 'EVALUAR'})
        sql ="""
                select det.name cabecera from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id in (%s) and det.puntua!=0
                group by det.name
                order by det.name
            """ % (start,stop,company_ids)

        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['cabecera']})
        return res

    def _get_puntuacion(self,start,stop,company_ids,indi_id):
        res=[]
        sql="""
                select det.name cabecera,avg(det.puntua) puntua from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id in (%s) and det.indicador_id=%s and det.puntua!=0
                group by det.name
                order by det.name
            """ % (start,stop,company_ids,indi_id)
        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['cabecera'], 'puntua': round(row['puntua'],2) })
        return res

    def _get_total(self,start,stop,company_ids):
        res=[]
        sql ="""
                select det.name cabecera, avg(det.puntua) totpunt from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id in (%s) and det.puntua!=0
                group by det.name
                order by det.name
            """ % (start,stop,company_ids)

        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['cabecera'], 'total': round(row['totpunt'],2)})
        return res

    def _get_companys(self):
        ids=[]
        sql = """select id as id ,name as nombre from res_company where  id in (select company_id from appcc ) group by id,name"""
        self.env.cr.execute(sql)
        rows = self.env.cr.dictfetchall()
        ids = ','.join(map(lambda y : str(y) , [x['id'] for x in rows]))
        return ids

    def _get_names_companys(self):
        res=[]
        sql = """select id as id ,name as nombre from res_company where  id in (select company_id from appcc ) group by id,name"""
        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['nombre'], 'id': row['id']})
        return res

    def _get_punt_company(self,start,stop,company_id):
        res=[]
        sql="""
                select det.name cabecera,avg(det.puntua) puntua from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id = %s  and det.puntua!=0
                group by det.name
                order by det.name
            """ % (start,stop,company_id)
        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'name': row['cabecera'], 'puntua': round(row['puntua'],2) })
        return res

    def _get_punt_company_mes(self,start,stop,company_id):
        res=[]
        sql="""
                select to_char(eval.fecha,'YYYY-MM') mes ,avg(det.puntua) puntua from appcc_evaluacion_detalle det
                join appcc_evaluacion_lineas lin on (lin.id = det.evallin_id)
                join appcc_evaluacion eval on (eval.id = lin.evaldet_id)
                where eval.fecha>=to_date('%s','YYYY-MM-DD') and eval.fecha<=to_date('%s','YYYY-MM-DD')
                and  eval.company_id = %s  and det.puntua!=0
                group by to_char(eval.fecha,'YYYY-MM')
                order by to_char(eval.fecha,'YYYY-MM')
            """ % (start,stop,company_id)

        self.env.cr.execute(sql)
        for row in self.env.cr.dictfetchall():
            res.append({'mes': row['mes'], 'puntua': round(row['puntua'],2) })
        return res

    def _get_registros_company(self,start,stop):
        registros_res = []
        i = 0
        reguni  = {}
        regini  = []
        columna = []
        cabcol  = []
        busca   = []
        total   = []
        totales = {}
        ids = self._get_companys()
        if ids:
            cabcol = self._get_cabecera_col(start, stop, ids)
            total  = self._get_total(start, stop, ids)
            for totcol in total:
                totales[totcol['name']] = totcol['total']
            acompany = self._get_names_companys()
            for colname_aux in cabcol:
                busca.append(colname_aux['name'])
            _colcab = {}
            for colname_aux in busca[1:]:
                _colcab[colname_aux] = '-'
            for row_company in acompany:
                obj_evadet = self._get_punt_company(start,stop,row_company['id'])
                if len(obj_evadet) != 0:
                    reguni = {"empresa": row_company['name']}
                    columna = _colcab.copy()
                    for det in obj_evadet:
                        for colname in busca[1:]:
                            if det['name'] == colname:
                                columna[det['name']] = det['puntua']
                                break

                    reguni['evals'] = columna
                    regini.append(reguni)
                    reguni = {}
            registros_res.append({'cabcol': cabcol, 'totevals': regini, 'cabrow': cabcol[1:], 'total': totales})
        return registros_res

    def _get_registros(self,start,stop):
        registros_res =[]
        i=0
        reguni  ={}
        regini  =[]
        columna =[]
        cabcol  =[]
        busca   =[]
        total   =[]
        totales ={}
        ids = self._get_companys()

        if ids:
            company_matriz_id= self.env['res.company'].sudo().search([('id','not in',ids.split(','))],limit=1)
            obj_indicador = self._get_indicador(start,stop,ids)
            #Revisamos para inicializar las cabeceras
            cabcol = self._get_cabecera_col(start,stop,ids)
            total  = self._get_total(start,stop,ids)
            #Normalizamos los totales por columnas
            for totcol in total:
                totales[totcol['name']]=totcol['total']

            for colname_aux in cabcol:
                busca.append(colname_aux['name'])
            _colcab={}
            for colname_aux in busca[1:]:
                _colcab[colname_aux] = '-'

            #Llenado de datos
            for indicador in obj_indicador:
                obj_evadet    = self._get_puntuacion(start,stop,ids,indicador["id"])
                if len(obj_evadet)!=0:
                    reguni = {"indicador": indicador['indicador']}
                    columna = _colcab.copy()
                    for det in obj_evadet:
                        for colname in busca[1:]:
                            if det['name']== colname:
                                columna[det['name']]  = det['puntua']
                                break

                    reguni['evals']=columna
                    regini.append(reguni)
                    reguni = {}

            registros_res.append({ 'cabcol': cabcol, 'totevals' : regini, 'cabrow': cabcol[1:], 'total':totales, 'company_id': company_matriz_id, 'start': start,'stop':stop,
                                   'rescomp': self._get_registros_company(start,stop), 'grafica' : [self.genera_grafica(start,stop)]})
            #print "------------3------------- %s" % registros_res

        return registros_res



    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs       = self.env[self.model].browse(self.env.context.get('active_id'))
        start = data['form']['used_context'].get('start')
        stop  = data['form']['used_context'].get('stop')
        registros_res      = self.with_context(data['form'].get('used_context',{}))._get_registros(start,stop)

        docargs = {
            'doc_ids'  : self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'evaluaciones': registros_res,


            }
        #print "------------5------------- %s" % docargs
        return self.env['report'].render('appcc.report_toteval_multi', docargs)



class ReportCertForma(models.AbstractModel):
    _name = 'report.appcc.report_certforma'

    def _get_cursos(self,tiposcursos_ids):


        if tiposcursos_ids:
            cursos  = tiposcursos_ids[0]
        else :
            cursos = None

        diccursos = []

        obj_curso   = self.env['appcc.maestros.tpcursos'].browse([cursos])
        obj_alumnos = self.env['appcc.planformacion'].search([('tiposcursos_ids','in',cursos)])
        if not obj_alumnos.exists():
            return diccursos
        company     = obj_alumnos[0].company_id
        eformadora  = obj_alumnos[0].tercero_id

        diccursos.append({'alumcursos':obj_alumnos,'tipocurso':obj_curso,'company_id':company,'forma':eformadora})
        return diccursos


    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        docs       = self.env[self.model].browse(self.env.context.get('active_id'))

        curso      = data['form'].get('curso_id',True)
        diccursos   = self.with_context(data['form'].get('used_context',{}))._get_cursos(curso)
        docargs = {
            'doc_ids'  : self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'alumnos': diccursos,
            }
        print "------------5------------- %s" % docargs
        return self.env['report'].render('appcc.report_certforma', docargs)

