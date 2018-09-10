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
from openerp import exceptions
from openerp import api, fields, models, fields
from openerp import _, tools
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
OPCIONES_TPCAL  = ([('FESTIVO NACIONAL',('FESTIVO NACIONAL')),('FESTIVO AUTONOMICO',('FESTIVO AUTONOMICO')),('FESTIVO LOCAL',('FESTIVO LOCAL'))])

OPCIONES_DIAS = ([('T',_('Ningun día')),('A',_('Todos los dias')),('L',_('Lunes a Viernes')),('F',_('Fin de Semana')),('5',_('Sabado')),('6',_('Domingo')),('0',_('Lunes')),('1',_('Martes')),('2',_('Miercoles')),('3',_('Jueves')),('4',_('Viernes'))])

FRECUENCIA    = [ ('daily', _('Day(s)') ), ('weekly', _('Week(s)')), ('monthly', _('Month(s)') ), ('yearly', _('Year(s)') ) ]

ALARMAS       = ([ (1, _('Email') ), (2, _('SMS')), (3, _('Email/SMS') ) ])



class AppccMColores(models.Model):
    _name = 'appcc.maestros.colores'
    _description= "Paleta de colores"

    name  = fields.Char(string="Nombre Color")
    color = fields.Char(string="Color en Hexadecimal")



class AppccMTipoPlanControl(models.Model):
    _name = 'appcc.maestros.tpplancontrol'
    _description = 'Actividades del appcc'


    name               = fields.Char(string=_("Denominación plan de control"))
    habilitaregistros  = fields.Boolean(index=True, default=False, string=_("Incluir en registros"))
    habilitanaliticas  = fields.Boolean(index=True, default=False, string=_("Incluir en analíticas"))
    habilitaformacion  = fields.Boolean( default=False, string=_("Incluir en formación"))
    habilitaavisos     = fields.Boolean(default=False, string=_("Incluir en  Avisos"))
    active             = fields.Boolean(string="Activo", default=True)



class AppccMCategorias(models.Model):
    _name = 'appcc.maestros.categorias'
    _description = 'Categorias de APPCC'

    name            = fields.Char(strin=_("Categoria"))
    active          = fields.Boolean(string=("Activa"), default=True)


#Instalamos segunda unida de ventas
class AppccMActividades(models.Model):
    _name = 'appcc.maestros.actividades'
    _description = 'Actividades del appcc'

    name            = fields.Char(string=_("Denominación"))
    tipo            = fields.Selection(([('V','Toma de valores'),('C','Check')]), required=True)
    colorback       = fields.Many2one('appcc.maestros.colores', string=_("Paleta de color de fondo") )
    colortxt        = fields.Many2one('appcc.maestros.colores', string =_("Paleta de color texto")   )
    agenda          = fields.Boolean(index=True, default=False, string=_("Incluir en agenda"))
    color           = fields.Char(related="colorback.color")
    actividades_ids = fields.One2many('appcc.maestros.actsonequip','actividades_id', string=_("No. Sondas"))
    active          = fields.Boolean(string="Activo", default=True)



class AppccMActividadesEquiposSondas(models.Model):
    _name = 'appcc.maestros.actsonequip'
    _description = 'Detalle de Actividades y Sondas'

    actividades_id = fields.Many2one('appcc.maestros.actividades')
    tracksonda_id  = fields.Many2one('tracksonda', string=_("Sonda"), required=True)
    equipo_id      = fields.Many2one('asset.asset', string=_("Equipos"), required=True)
    alarma         = fields.Selection(ALARMAS, string=_("Alarmas"))
    active         = fields.Boolean(string="Activo", default=True)



class AppccMParamanalisis(models.Model):
    _name = 'appcc.maestros.paraanalisis'
    _description = 'Definicion de Parametros Analizar'


    tipo          = fields.Selection(([('I',_('Indicador')),('S',_('Sustancia'))]), string=_("Tipo"), help=_("Tipo de valor"))
    name          = fields.Char(string=_("Denominacion"))
    unidades_id   = fields.Many2one('product.uom',string=_("Unidades"))
    active        = fields.Boolean(string="Activo", default=True)



class AppccMEtapas(models.Model):
    _name = 'appcc.maestros.etapas'
    _description = 'Definicion de Etapas'
    _sql_constraints = [
        ('uniq_name', 'unique(name)', "Ya se han generado etapas con esas caracteristicas, la etapas tiene que ser unicas!"),
        ]

    name        = fields.Char(string=_("Denominación"))
    ayuda       = fields.Text(string=_("Explicación"), required=False)
    inietap_id  = fields.Many2one('appcc.maestros.etapas','Etapa Inicial',ondelete='cascade',domain=[('parent_id', '=', False)],readonly=True, required=False)
    parent_id   = fields.Many2one('appcc.maestros.etapas', string=_('Etapa Padre'),domain="[('id','child_of',inietap_id)]",required=False)
    child_ids   = fields.One2many('appcc.maestros.etapas', 'parent_id', string=_('Subetapas'))
    active      = fields.Boolean(string="Activo", default=True)



class AppccMPeligros(models.Model):
    _name = 'appcc.maestros.peligros'
    _description = 'Definicion de Peligros'

    name        = fields.Char(string=_("Denominación"))
    ayuda       = fields.Text(string=_("Explicación"), required=False)
    active = fields.Boolean(string="Activo", default=True)



class AppccMTiposIndicador(models.Model):
    _name = 'appcc.maestros.tiposindicador'
    _description = 'Definicion de Tipos de Indicadores'

    name        =  fields.Char(string=_("Indicador"))
    indicador_id=  fields.Many2one('appcc.maestros.paraanalisis', string=_("Parámetro"), help=_("Parámetro de control"))
    vmax        =  fields.Float('Valor Maximo', digits=(5,2), required=True)
    vmin        =  fields.Float('Valor Minimo',digits=(5,2),required=True)
    active      =  fields.Boolean(string="Activo", default=True)
    tipocalculo =  fields.Selection([("N","S/C"),('TC',"Temp.Cinetica")], defaults="N")

    @api.one
    @api.constrains('vmin', 'vmax')
    def _check_vmax(self):
        if self.vmax < self.vmin:
            raise ValidationError('El valor máximo es menor que el mínimo')



class  stock_location(models.Model):
    _inherit ="stock.location"

    superficie         = fields.Integer( string=_("Superfice"), help  =_("Superfice en m2"))
    altura             = fields.Integer( string=_("Altura"), help  =_("Altura en metros"))
    volumen            = fields.Char(compute='_compute_volumen', help=_("Volumen en m3"))
    department_ids     = fields.Many2many('hr.department','hr_location_stock_rel','stock_location_id','department_id', "Departamento",domains=[('')])
    active             = fields.Boolean(string="Activo", default=True)


    @api.one
    def _compute_volumen(self):
        self.volumen = self.superficie * self.altura



class AppccMTiposMedidasActuacion(models.Model):
    _name = 'appcc.maestros.tpmedactuacion'
    _description = 'Definicion de Tipos de Medidas de Actuacion'

    name          = fields.Char(string=_("Medidas de actuación"))
    ayuda         = fields.Text(verbose_name=_("Ayuda"), required=False)
    tipo          = fields.Selection(selection=[("P","Preventiva"),("C","Correctora")] , string="Tipos de Medidas de Actuación" , required=True)
    solmante      = fields.Boolean(string="Genera Sol. Mante", help="General solicitud de mantenimiento en automatico",default=False )
    active        = fields.Boolean(string="Activo", default=True)



class AppccMTiposMedidasVigilancia(models.Model):
    _name = 'appcc.maestros.tpmedvigilancia'
    _description = 'Definicion de Tipos de Medidas de Vigilancia'

    name          = fields.Char(string=_("Medida de vigilancia"))
    ayuda         = fields.Text(verbose_name=_("Ayuda"), required=False)
    analitica     = fields.Boolean(string="Analitica ", help="Procede hacer Analiticas Microbiologicas", default=False)
    active        = fields.Boolean(string="Activo", default=True)



class AppccMTiposLimitesCriticos(models.Model):
    _name = 'appcc.maestros.tpmlimitescriticos'
    _description = 'Definicion de Tipos Limites Criticos'

    name          = fields.Char(string=_("Límites críticos"))
    ayuda         = fields.Text(verbose_name=_("Ayuda"), required=False)
    indicador_id  = fields.Many2one('appcc.maestros.tiposindicador', string=_("Indicador asociado al límite") )
    active        = fields.Boolean(string="Activo", default=True)



class AppccMTiposFrecuencias(models.Model):
    _name = 'appcc.maestros.tpfrecuencias'
    _description = 'Definicion de Tipos Limites Criticos'

    name           = fields.Char(string=_("Frecuencias"))
    nounidades     = fields.Integer( string=_("No. unidades"), help=_("No. de Unidades en Horas"))
    diaslaborables = fields.Selection(string=_("Excluir"),selection=[('T',_('Ningun día')),('A',_('Todos los dias')),('L',_('Lunes a Viernes')),('F',_('Fin de Semana')),('5',_('Sabado')),('6',_('Domingo')),('0',_('Lunes')),('1',_('Martes')),('2',_('Miercoles')),('3',_('Jueves')),('4',_('Viernes'))])
    rrule_type     = fields.Selection(string=_("Regla"), selection=FRECUENCIA)
    active         = fields.Boolean(string="Activo", default=True)



class ApccMTiposLegislacion(models.Model):
    _name = 'appcc.maestros.tplegislacion'
    _description = 'Definicion de Tipos de Legislacion'

    name          = fields.Char(string=_("Legislación"))
    ayuda         = fields.Text(verbose_name=_("Ayuda"), required=False)
    active        = fields.Boolean(string="Activo", default=True)



class AppccMTiposCursos(models.Model):
    _name = 'appcc.maestros.tpcursos'
    _description = 'Definicion de Tipos de Cursos'

    name           = fields.Char(string=_("Curso"))
    contenido      = fields.Text(verbose_name=_("Contenido"), required=False)
    legislacion_id = fields.Many2one('appcc.maestros.tplegislacion', string=_("Legislación"),required=True)
    active         = fields.Boolean(string="Activo", default=True)



class ApccMTiposTurnos(models.Model):
    _name = 'appcc.maestros.tpturnos'
    _description = 'Definicion de Tipos de Turnos'

    name     = fields.Char(string=_("Tipo de Turno"))
    ihora    = fields.Integer(string=_("Hora inicio"), help=_("En formato 24 horas"),default=0)
    fhora    = fields.Integer(string=_("Hora fin"), help=_("En formato 24 horas") ,default=24)
    active   = fields.Boolean(string="Activo", default=True)

    @api.one
    @api.constrains('fhora', 'ihora')
    def _check_fhora(self):

        if ( self.fhora <=24 and self.fhora>=0 and self.ihora <=24 and self.ihora>=0 ) == False :
            raise ValidationError( "El rango de hora tiene que estar entre 0 y 24")

        if self.fhora < self.ihora:
            raise ValidationError('La hora final no puede ser anterior a la hora inicial')



class AppccMExcepCalendar(models.Model):
    _name        = 'appcc.maestros.festivos'
    _description = "Alta de dias festivos y excepciones de calendario"


    name       = fields.Selection(OPCIONES_TPCAL,string=_("Tipo de excepción"), required=True)
    company_id = fields.Many2many('res.company',"company_id",string='Empresas' )
    fechaini   = fields.Date(string=_("Fecha inicio"), required=True)
    fechafin   = fields.Date(string=_("Fecha fin"), required=True)
    activo     = fields.Boolean(string=_("Activar"), default=True)

    @api.one
    @api.constrains('fechaini', 'fechafin')
    def _check_fecha(self):
        if self.fechafin < self.fechaini:
            raise ValidationError('Las fechas no corresponden a inicio y fin.')


