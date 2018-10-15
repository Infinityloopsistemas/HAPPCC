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
import base64
import openerp
from openerp import http
from openerp.http import request, route
from openerp.addons.web.controllers.main import serialize_exception,content_disposition

class tracksonsa_api_class(openerp.http.Controller):


    @route("/loaddata/device/", auth='public', type="http",  methods=['POST'], csrf=False)
    def write_tracksonda(self,**vals):
        """
        Protocol for Sensor Net Connect http://www.proges.com/schema/plugandtrack

        """
        if request.httprequest.method=='POST':
            header=request.httprequest.headers
            datos =  vals["owServerData"]
            root  = ET.fromstring(datos.read())
        reg={}
        address=""
        for i in range(16):
            if root[i].tag == 'MACAddress':
                address = root[i].text
            if i==0:
                reg={ root[i].tag.lower() : root[i].text }
            else:
                reg.update({ root[i].tag.lower() : root[i].text})

        #Alta del Sensor
        hub_obj        = request.env['tracksonda.hub']
        loaddatdev_obj = request.env['tracksonda.loaddatdev']
        tracksonda_obj = request.env['tracksonda']
        loaddatson_obj = request.env['tracksonda.loaddatson']
        res_hub        = hub_obj.search([('macaddress','=',address)])

        if res_hub:
            reg.update({'hub_id': int(res_hub[0].id) , 'company_id': int(res_hub[0].company_id.id) } )
            objidM=loaddatdev_obj.create(reg)
            idM= objidM.id
            reg={'loadatdev_id': idM }
            romid=""
            numsens = int(objidM.devicesconnected)
            sensores =[16,17,18]
            s=0
            for s in range(numsens):
                for i in range(8):
                    if root[sensores[s]][i].tag != 'RawData':
                        reg.update({root[sensores[s]][i].tag.lower() : root[sensores[s]][i].text})
                    if root[16][i].tag == 'ROMId':
                        romid =root[sensores[s]][i].text
                objsensor = tracksonda_obj.search([('romid','=',romid)])
                if objsensor:
                    reg.update({'tracksonda_id' : objsensor[0].id, 'company_id': int(res_hub[0].company_id.id) })
                    loaddatson_obj.create(reg)

            return str("200 OK")
        else:
            return str("ERROR 400")





