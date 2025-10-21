odoo.define('connector.flow.diff_view', function (require) {

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var QWeb = require('web.QWeb');
    var field_registry = require('web.field_registry');
    var rpc = require('web.rpc');


    //override existing
    var DiffView = AbstractField.extend({
        template: 'diff_view.widget',
        init: function () {
            this._super.apply(this, arguments);
        },
        destroy: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            return this._super.apply(this, arguments);
        },
        _render: function () {
            var self = this;
            this._super.apply(this, arguments);
            var diffString = this.record.data[this.name] || '';
            var parts = diffString.split("!#!#!#!##!#!#!#!!!#######!!!!!!#!#!#!");
            if (parts.length <= 1) {
                $(targetElement).html("no diff");
                return;
            }
            console.log(parts[0]);

            var targetElement = this.$el[0];
            var configuration = {
                drawFileList: false,
                //matching: 'lines'
                highlight: true,
                //outputFormat: 'side-by-side',
                outputFormat: 'line-by-line',
            };
            var diff = JsDiff['diffWords'](parts[0], parts[1]);
            var fragment = document.createDocumentFragment();
            for (var i = 0; i < diff.length; i++) {

                if (diff[i].added && diff[i + 1] && diff[i + 1].removed) {
                    var swap = diff[i];
                    diff[i] = diff[i + 1];
                    diff[i + 1] = swap;
                }

                var node;
                if (diff[i].removed) {
                    node = document.createElement('del');
                    node.appendChild(document.createTextNode(diff[i].value));
                } else if (diff[i].added) {
                    node = document.createElement('ins');
                    node.appendChild(document.createTextNode(diff[i].value));
                } else {
                    node = document.createTextNode(diff[i].value);
                }
                fragment.appendChild(node);
            }

            $(targetElement).html("");
            $("<pre/>").appendTo($(targetElement))[0].appendChild(fragment);
        },
    });
    field_registry.add('diff_view', DiffView); // as form widget
    return DiffView;

})
