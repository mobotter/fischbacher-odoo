odoo.define('contact_custom_fields.pos_partner_filter', function (require) {
    'use strict';

    const models = require('point_of_sale.models');
    const PosModelSuper = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            const partnerModel = this.models.find(m => m.model === 'res.partner');
            if (partnerModel) {
                partnerModel.domain = partnerModel.domain || [];
                partnerModel.domain.push(['sale_blocked', '=', false]);
            }
            return PosModelSuper.initialize.call(this, session, attributes);
        },
    });
});
