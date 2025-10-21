/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";

export class ListZbsyncListRenderer extends ListRenderer {
	setup() {
		super.setup(...arguments);
		this.rpc = useService('orm');
		this.actionService = useService('action');
	}
	async onCellClicked(record, column, ev) {
		const _super = super.onCellClicked();
		let res_id = record.data.id;
		if (record.resModel == "of.instance.item") {
			var action = await this.rpc.call(record.resModel, 'open', [res_id], {
				context: {
					instance_item_id: res_id,
					incoming: record.context.incoming,
					outgoing: record.context.outgoing,
				}
			});
			this.actionService.doAction(action);
			return;
		}
		else if (record.resModel == "of.base.item" || record.resModel == 'of.connection') {
			// add click event
			var $target = $(ev.target);
			if ($target[0].tagName === "BUTTON") {
				return;
			}
			if ($target.hasClass('open_line')) {
				var action = await this.rpc.call(record.resModel, 'open_line', [res_id]);
				this.actionService.doAction(action, {
					onClose: async () => {
						await record.model.root.load();
						record.model.notify();
					}
				});
			}
			else {
				var action = await this.rpc.call(record.resModel, 'open', [res_id], {
					context: {
						instance_item_id: res_id,
						inout: record.context.inout,
					}
				});
				this.actionService.doAction(action);
			}
			return;
		}
		_super(...arguments);
	}
}