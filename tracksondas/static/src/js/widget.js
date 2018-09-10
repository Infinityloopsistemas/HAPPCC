odoo.define('general_template.color', function(require) {
    "use strict";


    var core = require('web.core');
    var form_widgets = require('web.form_widgets');
    var FormView = require('web.FormView');

    var _t = core._t;


    var _super_getDir = jscolor.getDir.prototype;
    jscolor.getDir = function() {
        var dir = _super_getDir.constructor();
        if (dir.indexOf('web_widget_color') === -1) {
            jscolor.dir = 'general_template/static/lib/jscolor/';
        }
        return jscolor.dir;
    };

    //instance.web.search.fields.add('color', 'instance.web.search.CharField');
    core.search_widgets_registry.add('color', 'instance.web.search.CharField');
    var FieldColor = form_widgets.FieldChar.extend({
        template: 'FieldColor',
        widget_class: 'oe_form_field_color',
        store_dom_value: function() {
            if (!this.get('effective_readonly') && this.$('input').length && this.is_syntax_valid()) {
                this.internal_set_value(
                    this.parse_value(
                        this.$('input').val()));
            }
        },
        is_syntax_valid: function() {
            var $input = this.$('input');
            if (!this.get("effective_readonly") && $input.size() > 0) {
                var val = $input.val();
                var isOk = /^#[0-9A-F]{6}$/i.test(val);
                if (!isOk) {
                    return false;
                }
                try {
                    this.parse_value(this.$('input').val(), '');
                    return true;
                } catch (e) {
                    return false;
                }
            }
            return true;
        },
        render_value: function() {
            var show_value = this.format_value(this.get('value'), '');
            if (!this.get("effective_readonly")) {
                var $input = this.$el.find('input');
                $input.val(show_value);
                $input.css("background-color", show_value)
                jscolor.init(this.$el[0]);
            } else {
                this.$(".oe_form_char_content").text(show_value);
                this.$('div').css("background-color", show_value)
            }
        }
    });

    core.form_widget_registry.add('color', FieldColor);

    /*
     * Init jscolor for each editable mode on view form
     */
    FormView.include({
        to_edit_mode: function() {
            this._super();
            jscolor.init(this.$el[0]);
        }
    });
});