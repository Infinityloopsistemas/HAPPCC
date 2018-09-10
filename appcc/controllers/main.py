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
import xml.etree.ElementTree as ET
from time import sleep
import openerp
from openerp.exceptions import UserError, ValidationError
from openerp.http import request, route, redirect_with_hash
import json
import datetime
import logging

# FORMATO JSON
# {"jsonrpc": "2.0",
#  "method": "call",
#  "params": {"context": {},
#             "login": "admin", "password": "", "db": ""},
#  "id": null}



_logger = logging.getLogger(__name__)

class appcc_mobile_rest_api(openerp.http.Controller):


    @route("/appcc/login", type='json', auth='public', methods=['POST'], csrf=False)
    def get_login(self,login,password,db):
        uid = request.session.authenticate(db, login, password)
        if uid is not False:
            return request.csrf_token()
        return  "Wrong login/password"



    def _validacionRegistros(self,reg,fecreg,uid):
            # Iniciamos busquedad registro inmediatamente anterior:
            # Salta la validaciones para las sondas
            objreg = request.registry.get('appcc.registros')
            reg.incidencia = False
            start_date=fecreg
            fmt = '%Y-%m-%d'
            frec = reg.detreg_id.frecuencia_id.nounidades / 24
            diaejecuta =  reg.detreg_id.diaejecuta
            iddetreg   =  reg.detreg_id.id
            sql = """select max(start_date) ufecha from appcc_registros where state='done' and detreg_id= %s and start_date!=to_date('%s','YYYY-MM-DD')  """ % (
            reg.detreg_id.id, start_date)
            # print sql
            cr = request.env.cr
            cr.execute(sql)
            regist = cr.dictfetchall()
            row = regist[0]
            numdias = 0
            dfecha = row['ufecha']
            if dfecha:
                listregs= objreg.search(request.cr, uid, [('detreg_id', '=', iddetreg)], order='start_date')
                for row in objreg.browse(request.cr, uid, listregs):
                    if not row.state == 'done' and row.start_date < start_date:
                        if row.start_date:
                            return row.start_date
                        else:
                            return " "
            else:
                sql = """select min(start_date) ufecha, min(tipo) utipo from appcc_registros where state!='done' and detreg_id= %s  """ % (
                reg.detreg_id.id)
                cr = request.env.cr
                cr.execute(sql)
                regist = cr.dictfetchall()
                row = regist[0]
                if row['ufecha']:
                    if row['ufecha'] != start_date:
                        if row['ufecha']:
                            return row['ufecha']
                        else:
                            return " "
                    else:
                        return " "
                else:
                    return " "


    @route("/appcc/registros", type='json', auth='public', methods=['POST'], csrf=False)
    def get_registro(self, login, password, fecreg, db):
        uid = request.session.authenticate(db, login, password)
        if uid is not False:
            request.uid = uid
            if fecreg:
                fecha_ini=fecreg
                fecha_fin=fecreg
            else:
                fecha_ini = (datetime.datetime.now().date() + datetime.timedelta(days=-7)).strftime("%Y-%m-%d")
                fecha_fin = (datetime.datetime.now().date() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            print "uid que se obtiene %s" % request.uid
            ajson = []
            objdetreg = request.registry.get('appcc.detallesregistros')
            objreg    = request.registry.get('appcc.registros')
            objfirmas = request.registry.get('appcc.registros.firmas')
            objemple  = request.registry.get('hr.employee')
            idsemple  = objemple.search(request.cr, uid, [('user_id', '=', uid)])
            #Buscamos id empleado asociado a usuario
            idsdepts = map(lambda x : x , ( reg.department_id.id  for reg in objemple.browse(request.cr, uid,idsemple)))
            firmado="N"
            #Buscar si existe firma para devolver S o N
            print "Ids de firmas %s" % idsdepts
            if idsdepts:
                reg_firma = objfirmas.search(request.cr, uid,[('firma_id.department_id.id','in',idsdepts),('fecha_rel','=',fecreg)])
                print reg_firma
                if reg_firma:
                    firmado="S"
                else:
                    firmado="N"

            registros_res = []
            regs_detreg = objdetreg.search(request.cr, uid, [('actividades_id.agenda', '=', True),('departamento_ids.member_ids.user_id', 'in',[uid]) ])
            for detregid in objdetreg.browse(request.cr, uid, regs_detreg):
                reguni = {}
                regdet = []
                vmax = detregid.indicador_id.vmax
                vmin = detregid.indicador_id.vmin
                # reguni[detregid.id] = {'id': detregid.id,'name': detregid.name}
                #Parametrizamos 8 dias de registros
                regs = objreg.search(request.cr, uid, [('start_date', '>=', fecha_ini),('start_date','<=',fecha_fin) , ('detreg_id', '=', detregid.id)])
                for reg in objreg.browse(request.cr, uid, regs):
                    if reguni == {}:
                        # Solo crea registros si ese dia existen
                        reguni["cab"] ={'cabdid': detregid.id, 'name': detregid.name, 'qr': detregid.tpadquisicion,  'equipo': detregid.equipos_id.name, 'serial': detregid.equipos_id.serial,
                                         'vmax': vmax , 'vmin':  vmin   ,  'zona': detregid.zonas_id.name, 'actividades': detregid.actividades_id.name, 'orden': detregid.ordagenda, 'indicador': detregid.indicador_id.name, "firmado":firmado }


                    fecpend = self._validacionRegistros(reg,fecreg,uid)
                    if not fecpend:
                        fecpend=" "

                    regdet.append( { 'fecpend': fecpend, 'detid': reg.id, 'start_date': reg.start_date, 'valor': reg.valor,
                                                   'estado': reg.estado, 'state': reg.state or ' ', 'tipo': reg.tipo, 'observa': (reg.observaciones  if reg.observaciones else " " )})
                if reguni != {}:
                    reguni["cab"]["det"] = regdet
                    registros_res.append(reguni)
            _logger.info("Resultado registro: %s " % registros_res)
            return registros_res
        return ["Wrong login/password"]

    @route("/appcc/registros/actualizar", type='json', auth='public', methods=['POST'], csrf=False)
    def get_registros(self, login, password, db,  datos):
        uid = request.session.authenticate(db, login, password)

        registros= json.loads(datos)
        _logger.info("Recepcion de registro: %s " % registros)

        if uid is not False:
            request.uid = uid
            ajson     = []
            objreg    = request.registry.get('appcc.registros')
            registros_res = []
            for reg in registros:
                print reg
                if  reg["tipo"]== "C":
                    valor = True if reg["estado"]==1 else False
                    actua={"estado": valor,"observaciones":reg["observa"], "device": reg["device"]}
                else:
                    valor = reg["valor"]
                    if type(valor) == str:
                        valor = float(valor)
                    actua={"valor" : valor ,"observaciones":reg["observa"],"device": reg["device"] }

                objactua = objreg.browse(request.cr, uid, reg["id"])[0]
                try:
                    if reg["tipo"] != objactua.detreg_id.actividades_id.tipo:
                        return "Error, Incongruencia en tipo valor/check"

                    _logger.info("String para actualizar %s " % actua)
                    objactua.write(actua)

                    #S solo genera aviso
                    #M genera aviso con solicitud de mantenimiento
                    if reg.get("aviso",'N') == "S":
                        objactua.action_button_incidencia()
                    if reg.get("aviso","N") == "M":
                        objactua.action_solincide_tablet()
                except Exception as e:
                     print e[0]
                     return "Error: %s " % e[0]

            _logger.info("Resultado registro: %s " % registros)
            return "Ok"

        return "Wrong login/password"

    @route("/appcc/registros/pendientes", type='json', auth='public', methods=['POST'], csrf=False)
    def get_pendientes(self, login, password, db, mes, ano):
        uid = request.session.authenticate(db, login, password)
        if uid is not False:
            request.uid = uid
            #Calcular mes inicio dia inicio mes y dia fin mes
            now = datetime.datetime.now()
            next_month     = datetime.datetime(year=ano, month=mes + 1, day=1)
            last_day_month = next_month - datetime.timedelta(days=1)
            fecha_ini = datetime.datetime(year=ano,month=mes,day=1).strftime("%Y-%m-%d")
            fecha_fin = datetime.datetime(year=ano,month=mes,day=last_day_month.day).strftime("%Y-%m-%d")
            ajson = []
            objdetreg = request.registry.get('appcc.detallesregistros')
            objreg = request.registry.get('appcc.registros')
            registros_res = []
            #regs_detreg = objdetreg.search(request.cr, uid, [('actividades_id.agenda', '=', True),
            #                                              ('departamento_ids.member_ids.user_id', 'in', [uid])])

            regs = objreg.search_read(request.cr, uid, [('start_date', '>=', fecha_ini), ('start_date', '<=', fecha_fin),
                                                     ('detreg_id.departamento_ids.member_ids.user_id', 'in', [uid])
                                                    ,('detreg_id.actividades_id.agenda', '=', True),('state', '=', False)],['start_date'] )

            list_fechas=[]
            for rowfec in regs:
                list_fechas.append(rowfec["start_date"])

            fechas =  [i for n, i in enumerate(list_fechas) if i not in list_fechas[n + 1:]]

            for fec_reg in fechas:
                regs = objreg.search(request.cr, uid, [('start_date', '=', fechas), ('state', '=', False)])
                reguni = {}
                regdet = []
                reguni["cab"] ={'start_date': fec_reg }
                registros_res.append(reguni)

            
            return registros_res
        return ["Wrong login/password"]



    @route("/appcc/empleados", type='json', auth='public', methods=['POST'], csrf=False)
    def get_empleados(self, login, password, fecreg, db):
        uid = request.session.authenticate(db, login, password)
        if uid is not False:
            request.uid = uid
            objdetreg = request.registry.get('appcc.detallesregistros')
            objemp = request.registry.get('hr.employee')
            # Conseguimos todos los detalles de registros asociados al departamento del usuario.
            fecha = fecreg
            print "Fecha %s" % fecha
            regs = objdetreg.search_read(request.cr, uid, [('detreg_ids.start_date', 'in', [fecha]),
                                                           ('departamento_ids.member_ids.user_id', 'in', [uid])
                , ('actividades_id.agenda', '=', True)], ['departamento_ids'])

            list_depart = []
            for rowdept in regs:
                list_depart.append(rowdept["departamento_ids"])

            departaments = [i for n, i in enumerate(list_depart) if i not in list_depart[n + 1:]]

            empleados = []
            if len(departaments) != 0:
                for empname in objemp.search_read(request.cr, uid,
                                                  [("department_id", "in", departaments[0]), ('firmaregappcc', '=', True)],
                                                  ['name']):
                    empleados.append({'name': empname['name'], 'idemple': empname["id"]} )
            if empleados:
                return empleados
            else:
                return ["Sin empleados autorizados firma"]

        return ["Wrong login/password"]


    @route("/appcc/logocompany", type='json', auth='public', methods=['POST'], csrf=False)
    def get_logocompany(self, login, password, db, idappcc):

        uid = request.session.authenticate(db, login, password)
        if uid is not False:
            request.uid = uid
            objappcc = request.registry.get('appcc')
            objcompa = request.registry.get('res.company')
            appcc = objappcc.browse(request.cr, uid, [idappcc])[0]
            company = objcompa.browse(request.cr, uid, [appcc.company_id.id])[0]
            if company.logo_web:

                return [{ "logo" : company.logo_web }]
            else:
                return[ {"logo" : " "}]

        return ["Wrong login/password"]


    @route("/appcc/registros/firmas", type='json', auth='public', methods=['POST'], csrf=False)
    def get_firmas(self, login, password, db, imagen,idemp,fecha):
        uid = request.session.authenticate(db, login, password)
        if uid is not False:
            request.uid = uid
            objfirmas   = request.registry.get('appcc.registros.firmas')
            objdetreg   = request.registry.get('appcc.detallesregistros')
            objreg      = request.registry.get('appcc.registros')
            regs_detreg = objdetreg.search(request.cr, uid, [('actividades_id.agenda', '=', True),
                                                             ('departamento_ids.member_ids.user_id', 'in', [uid])])
            for detregid in objdetreg.browse(request.cr, uid, regs_detreg):
                regs = objreg.search(request.cr, uid, [('start_date', '=', fecha),
                                                       ('detreg_id', '=', detregid.id)])
                for reg in objreg.browse(request.cr, uid, regs):
                    reg.write(  {'firmas_id': idemp } )

            try:
                newid = objfirmas.create(request.cr, uid, {"image": imagen, "fecha_rel": fecha, "firma_id": idemp })
                return "Ok"
            except Exception as e:
                     return "Error: %s " % e[0]


        return "Wrong login/password"



