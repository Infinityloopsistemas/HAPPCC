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

from dateutil.relativedelta import relativedelta
from openerp import api, fields, models
from openerp.exceptions import UserError
from openerp import _, tools



class AppccDetRegQR(models.TransientModel):
    _name = 'appcc.report.reg.qr'
    _description = 'Report Detalles Registros QR'

    detreg_id = fields.Many2many('appcc.detallesregistros', string=_("Tipo de registros"), domain=lambda self: [
        ('company_id.id', '=', self.env['res.company']._company_default_get('appcc.detallesregistros').id)])

    @api.one
    @api.constrains('detreg_id')
    def _check_detreg(self):
        if not self.detreg_id:
            raise Warning("Seleccione un registro")

    def _build_contexts(self, data):
        result = {}
        result['detreg_id'] = data['form']['detreg_id'] or False
        return result

    def _print_report(self, data):
        print "Mandamos a imprimir"
        return self.env['report'].with_context(landscape=False).get_action(self, 'appcc.report_detreg_qr', data=data)

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['detreg_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang', 'en_ES'))
        return self._print_report(data)



class AppccRegistrosReport(models.TransientModel):
    _inherit = 'appcc.common.report'
    _name    = 'appcc.report.reg'
    _description = 'Report comunes registros'


    detreg_id = fields.Many2many('appcc.detallesregistros', string=_("Tipo de registros"), domain = lambda self: [('company_id.id','=', self.env['res.company']._company_default_get('appcc.detallesregistros').id)])

    @api.multi
    def pre_print_report(self, data):

        data['form'].update(self.read(['detreg_id'])[0])
        data['form'].update()
        return data


    def _print_report(self, data):
        data = self.pre_print_report(data)
        if not data['form'].get('date_to') or not data['form'].get('date_from'):
            raise UserError( ("Debe introducir una fecha de inicio y una fecha de fin"))
        if not data['form']['detreg_id']:
            raise UserError( ("Seleccione un detalle de registro"))

        return self.env['report'].with_context(landscape=False).get_action(self, 'appcc.report_regfecha', data=data)



class AppccRegEvalReport(models.TransientModel):
    _inherit     = 'appcc.common.report'
    _name        = 'appcc.report.evalreg'
    _description = 'Reporte de evaluaciones incluyendo registros asociados al equipo'


    equipo_id     = fields.Many2one('asset.asset', string=_("Equipos"),  company_dependent=True)
    frecuencia_id = fields.Many2one('appcc.maestros.tpfrecuencias', string=_("Frecuencia"))
    evallin_id    = fields.Many2one('appcc.evaluacion.lineas', domain=[(('property_equipos', '!=', False ))])

    @api.onchange('date_to','date_from')
    def onchange_fechas(self):
        res={}
        idsrow=[]

        if not res.get('domain',{}):
            obj_evallin_ids = self.env['appcc.evaluacion.lineas'].search_read(
                              [ ('fecha', '>=', self.date_from), ('fecha', '<=', self.date_to)], ['property_equipos'])
            #print obj_evallin_ids
            for rowlins in obj_evallin_ids:
                idsrow.append(rowlins["property_equipos"][0])


            if len(idsrow)!=0:
                res['domain'] = {'equipo_id': [('id', 'in', idsrow)]}

        return res

    @api.onchange('equipo_id')
    def onchange_equipo_id(self):
        res = {}
        cabregs_ids=[]
        frecs_ids=[]
        if not res.get('domain', {}):
            evallin_ids = self.env['appcc.evaluacion.lineas'].search(
                [('property_equipos','=',self.equipo_id.id),('fecha', '>=', self.date_from), ('fecha', '<=', self.date_to)])
            print evallin_ids
            for objids in evallin_ids:
                cabregs_ids.append(objids.id)
            res['domain'] = {'evallin_id': [('id', 'in', cabregs_ids)]}
            print "Equipos"
            print res
        return res

    @api.onchange('evallin_id')
    def onchange_evallin(self):
        res = {}
        frecs_ids = []
        if not res.get('domain', {}):
            if self.evallin_id:
                # _sql="""select frecuencia_id from appcc_detallesregistros
                #         where cabreg_id =%s and equipos_id=%s
                #         group by frecuencia_id""" % (,self.equipo_id)
                # self.env.cr.execute(_sql)
                # print _sql
                # rows = self.env.cr.dictfetchall()
                # ids = ','.join(map(lambda y: str(y), [x['frecuencia_id'] for x in rows]))
                # ids_frecs = ids.split(",")
                # print ids_frecs
                obj_detregs=self.env['appcc.detallesregistros'].search([('cabreg_id','=',self.evallin_id.evaldet_id.regeval_id.id),('detreg_ids','!=',False),
                                                                        ('equipos_id','=',self.equipo_id.id)] )
                for objfre in obj_detregs:
                    frecs_ids.append(objfre.frecuencia_id.id)
                res['domain'] ={'frecuencia_id' : [('id','in',frecs_ids)]}
        else:
            res['domain'] = {'frecuencia_id': [('id', '=', 0)]}
        return res

    @api.multi
    def pre_print_report(self, data):
        print "------------1------------- %s" % data
        data['form'].update(self.read(['evallin_id'])[0])
        data['form'].update(self.read(['frecuencia_id'])[0])
        data['form'].update(self.read(['equipo_id'])[0])
        data['form'].update()
        return data

    def _print_report(self, data):
        data = self.pre_print_report(data)
        print "------------2------------- %s" % data
        if not data['form'].get('date_to') or not data['form'].get('date_from'):
            raise UserError(("Debe introducir una fecha de inicio y una fecha de fin"))
        if not data['form']['evallin_id']:
            raise UserError(("Seleccione una evaluacion"))
        if not data['form']['equipo_id']:
            raise UserError(("Seleccione un equipo"))
        # if not data['form']['frecuencia_id']:
        #     raise UserError(("Seleccione una frecuencia"))

        return self.env['report'].with_context(landscape=False).get_action(self, 'appcc.report_evalreg', data=data)



class AppccTotEvalReport(models.TransientModel):
    _name = 'appcc.report.toteval'
    _description = 'Reporte de resumen de evaluaciones'

    period_length = fields.Integer(string='Longitud Periodo (dias)', required=True, default=30)
    date_from = fields.Date(string="Fecha desde", default=lambda *a: time.strftime('%Y-%m-%d'))

    @api.one
    @api.constrains('period_length','date_from')
    def _check_valida(self):
        if self.period_length <= 0:
            raise UserError(_('El periodo tiene que ser mayor que 0'))
        if not self.date_from:
            raise UserError(_('Debe comenzar con una fecha'))

    def _build_contexts(self, data):
        result = {}
        datos =data['form']
        period_length = datos['period_length']
        start = datetime.strptime(datos['date_from'], "%Y-%m-%d")
        stop = start + relativedelta(days=period_length)
        result['start'] = start.strftime("%Y-%m-%d")
        result['stop']  = stop.strftime("%Y-%m-%d")
        return result

    def _print_report(self, data):
        return self.env['report'].with_context(landscape=True).get_action(self,'appcc.report_toteval_res', data=data)

    @api.multi
    def check_report(self,data):
        self.ensure_one()
        data={}
        data['ids']   = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form']  = self.read(['date_from','period_length'])[0]
        used_context  = self._build_contexts(data)
        data['form']['used_context'] =dict(used_context, lang=self.env.context.get('lang', 'en_ES'))
        return self._print_report(data)



class AppccTotEvalReportMulti(models.TransientModel):
    _name = 'appcc.report.totevalm'
    _description = 'Reporte multi Local de resumen de evaluaciones'

    period_length = fields.Integer(string='Longitud Periodo (dias)', required=True, default=30)
    date_from = fields.Date(string="Fecha desde", default=lambda *a: time.strftime('%Y-%m-%d'))

    @api.one
    @api.constrains('period_length','date_from')
    def _check_valida(self):
        if self.period_length <= 0:
            raise UserError(_('El periodo tiene que ser mayor que 0'))
        if not self.date_from:
            raise UserError(_('Debe comenzar con una fecha'))

    def _build_contexts(self, data):
        result = {}
        datos =data['form']
        period_length = datos['period_length']
        start = datetime.strptime(datos['date_from'], "%Y-%m-%d")
        stop = start + relativedelta(days=period_length)
        result['start'] = start.strftime("%Y-%m-%d")
        result['stop']  = stop.strftime("%Y-%m-%d")
        return result

    def _print_report(self, data):
        return self.env['report'].with_context(landscape=True).get_action(self,'appcc.report_toteval_multi', data=data)

    @api.multi
    def check_report(self,data):
        self.ensure_one()
        data={}
        data['ids']   = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form']  = self.read(['date_from','period_length'])[0]
        used_context  = self._build_contexts(data)
        data['form']['used_context'] =dict(used_context, lang=self.env.context.get('lang', 'en_ES'))
        return self._print_report(data)



class AppccCertFormaReport(models.TransientModel):
    _inherit = 'appcc.common.report'
    _name    = 'appcc.report.certforma'
    _description = 'Report certificados formativos grupales'

    curso_id  = fields.Many2one('appcc.maestros.tpcursos',string="Curso Recibido")

    @api.multi
    def pre_print_report(self, data):
        print "------------1------------- %s" % data
        data['form'].update(self.read(['curso_id'])[0])
        data['form'].update()
        return data

    def _print_report(self, data):
        data = self.pre_print_report(data)
        print "------------2------------- %s" % data
        if not data['form']['curso_id']:
            raise UserError( ("Seleccione un tipo de curso"))

        return self.env['report'].with_context(landscape=False).get_action(self, 'appcc.report_certforma', data=data)
