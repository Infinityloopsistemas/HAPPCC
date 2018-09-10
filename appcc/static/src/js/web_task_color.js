odoo.define('appcc.appcc_calendar', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var pyeval = require('web.pyeval');
    var CalendarView = require('web_calendar.CalendarView');

    var _t = core._t;
    var QWeb = core.qweb;

    CalendarView.include({
        event_data_transform: function (event) {
            var res = this._super.apply(this, arguments);
            /* if (res && res.hasOwnProperty('className')) {
                res.backgroundColor = '#DBDBDB';
            }*/
            res.backgroundColor = event["color"];
            if (event["state"]=="done") {
                res.backgroundColor = '#DBDBDB';
            }
            if (event["state"]=="draft"){
                res.backgroundColor = "#ff0000";
            }
            //Para hacer legible la tarea en la agenda
            if( res.title.length >75 )
            {
                var titulos = res.title.split("-")
                res.title=titulos[1]
            }
            console.log(res.title)
            return res;
        }
    });

});