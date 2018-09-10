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
__author__ = 'julian'
from openerp.osv import osv
from openerp import api, fields, models, fields
from openerp import _, tools
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
import datetime
PUNTUACION  =    map( lambda x: 2*[ (str(x))] , range(0,11) )

class AppccTemplateEvaluacion(models.Model):
    _name        = 'appcc.template.evaluacion'
    _description = 'Configuracion de Plantillas para evaluacion'

    name            = fields.Char(string=_("Nombre plantilla"),  required=True)
    fecha           = fields.Date(string=_("Fecha"))
    tipo            = fields.Selection([('D','DEPARTAMENTOS'),('P','PERSONAL'),('C','CENTRO'),('E','EQUIPOS'),('O','OTROS')], string=_("Tipos de evaluación"))
    company_id      = fields.Many2many('res.company', 'appcc_tmplateval_company_rel','tevaluacion_id','company_id', string="Empresa" )
    tevaluacion_ids = fields.One2many('appcc.template.evaluador','tevaluacion_id')
    active          = fields.Boolean(string=_("Activa"), default=True)



class AppccTemplateEvaluador(models.Model):
    _name        = 'appcc.template.evaluador'
    _description = 'Indicador de la evaluacion'

    name            = fields.Char(string=_("Verificación"), required=True)
    tevaluacion_id  = fields.Many2one('appcc.template.evaluacion')
    puntuable       = fields.Boolean(string=_("Puntuable"),default=False)
    active          = fields.Boolean(string=_("Activa"), default=True)



class AppccEvaluacion(models.Model):
    _name        = 'appcc.evaluacion'
    _description = 'Evaluaciones'

    fecha             = fields.Date(string=_("Fecha"))
    secuencia         = fields.Char(string=_("REF."))
    name              = fields.Char(string=_("Denominacion Evaluacion"),  required=True)
    tecnicos_id       = fields.Many2one('res.partner',string=_("Tecnicos"), domain=([('company_type','=','person'),('category_id.name','=','VETERINARIO')]))
    company_id        = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env['res.company']._company_default_get('appcc..evaluacion'))
    evaldet_ids       = fields.One2many('appcc.evaluacion.lineas','evaldet_id', oncopy="cascade")
    calevalua_id      = fields.Many2one("calendar.event",copy=False)
    regeval_id        = fields.Many2one('appcc.cabregistros',string=_("Registros Control"),copy=False)

    @api.multi
    def unlink(self):
        objevent = self.mapped('calevalua_id')
        ret = super(AppccEvaluacion, self).unlink()
        objevent.unlink()
        return ret

    @api.one
    def copy(self, default=None):
        default = dict(default or {}, name=_("%s (Copia)") % self.name)
        return super(AppccEvaluacion, self).copy(default=default)


class AppccLinEvaluacion(models.Model):
    _name        = 'appcc.evaluacion.lineas'
    _description = 'Evaluaciones Lineas'
    _rec_name    = 'evaldet_id'

    @api.multi
    @api.onchange('evaldet_id','property_departament','property_employee','property_centro','property_equipos')
    def _get_entidad(self):
        for obj in self:
                if  obj.property_departament:
                    obj.name = obj.property_departament.name
                elif obj.property_employee:
                    obj.name =  obj.property_employee.name
                elif obj.property_centro:
                    obj.name = "CENTRO"
                elif obj.property_equipos:
                    obj.name = obj.property_equipos.name

    evaldet_id           = fields.Many2one('appcc.evaluacion')
    fecha                = fields.Date(related="evaldet_id.fecha", string=_("Fecha"))
    company_id           = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env['res.company']._company_default_get('appcc.evaluacion.lineas'))
    templatevalua_id     = fields.Many2one('appcc.template.evaluacion',string=_("Plantilla"), required=True)
    property_departament = fields.Many2one('hr.department', string=_("Departamento"),company_dependent=True,copy=False)
    property_employee    = fields.Many2one('hr.employee',   string=_("Personal")    ,company_dependent=True,copy=False)
    property_centro      = fields.Many2one('res.partner',   string=_("Centro")      ,company_dependent=True,copy=False)
    property_equipos     = fields.Many2one('asset.asset',   string=_("Equipos")     ,company_dependent=True,copy=False)
    name                 = fields.Char(string=_("Denominación"),copy=False, compute='_get_entidad', store=True)
    evallin_ids          = fields.One2many('appcc.evaluacion.detalle','evallin_id')
    totpuntuacion        = fields.Float(compute='_calculo_puntuacion', store=True, string=_("Punt.Media"))

    @api.model
    def create(self, vals):
        if not vals.get('property_departament') and not vals.get('property_employee') and not vals.get('property_centro') and not vals.get('property_equipos'):
            raise ValidationError("NO SE CREA, NO EXISTE TIPO DE EVALUACION ASIGNADA")

        new_id = super(AppccLinEvaluacion, self).create(vals)
        return new_id

    @api.multi
    def action_button_renombrar(self):
        for row in self:
            if row.property_departament:
                name = row.property_departament.name
            elif row.property_employee:
                name = row.property_employee.name
            elif row.property_centro:
                name = "CENTRO"
            elif row.property_equipos:
                name = row.property_equipos.name
            self.name = name
            for drow in row.evallin_ids:
                print drow
                drow.write({'name': name})


    @api.one
    @api.depends('evallin_ids')
    def _calculo_puntuacion(self):
        puntua = 0
        i      = 0
        npunt   = float(len(self.evallin_ids))
        if npunt!=0:
            self.totpuntuacion = sum(int(line.puntuacion) for line in self.evallin_ids)/npunt
        else:
            self.totpuntuacion=0



    @api.multi
    def unlink(self):
        objeval    = self.mapped('evaldet_id')
        for regsdet in self:
            for reg in regsdet.evallin_ids:
                reg.unlink()
        ret= super(AppccLinEvaluacion,self).unlink()
        objeval.unlink()
        return ret



class AppccDetEvaluacion(models.Model):
        _name        = 'appcc.evaluacion.detalle'
        _description = 'Evaluaciones Detalles'

        @api.one
        @api.onchange('evallin_id','observa')
        def _get_entidad(self):
            if self.evallin_id.property_departament:
                self.name = self.evallin_id.property_departament.name
            if self.evallin_id.property_employee:
                self.name = self.evallin_id.property_employee.name
            if self.evallin_id.property_centro:
                self.name = "CENTRO"
            if self.evallin_id.property_equipos:
                self.name = self.evallin_id.property_equipos.name

        evallin_id      = fields.Many2one('appcc.evaluacion.lineas')
        indicador_id    = fields.Many2one('appcc.template.evaluador', domain=[('tevaluacion_id','=','evallin_id.templatevalua_id.id')],string=_("Verificación"))
        textoevaluar    = fields.Char(related="indicador_id.name", string=_("Evaluar Desc."))
        puntuacion      = fields.Selection(PUNTUACION,string=_("Puntuación"))
        siono           = fields.Selection([('Si','Si'),('No','No'),('O','Obs')] ,string="Estado")
        puntua          = fields.Float(compute='_to_float',store=True,  group_operator="avg")
        observa         = fields.Text(string=_("Obser."))
        puntuable       = fields.Boolean(related="indicador_id.puntuable")
        company_id      = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env['res.company']._company_default_get('appcc.evaluacion.detalle'))
        name            = fields.Char(string=_("Entidad a evaluar"))
        grupoevaluador  = fields.Char(compute='_get_grupoeval', store=True)


        @api.one
        @api.depends('evallin_id')
        def _get_grupoeval(self):
             self.grupoevaluador = self.evallin_id.evaldet_id.name

        @api.one
        @api.depends('puntuacion','puntua')
        def _to_float(self):
             self.puntua = int(self.puntuacion)

