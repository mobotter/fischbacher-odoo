# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import models


class Connection(models.Model):
    _inherit = "of.connection"

    def applies(self, instance_item):
        if self._evals_zync_record:
            records = self._retrieve_zync_records(instance_item)
            filtered_records = self._filter_records(
                instance_item, records, stop_on_match=True
            )
            return bool(filtered_records)
        else:
            return super().applies(instance_item)

    @property
    def _evals_zync_record(self):
        return any(x in (self.condition or "") for x in ["zync_record", "record"])

    def _retrieve_zync_records(self, instance_item):
        zyncpipelines = []

        if (
            instance_item.item_id.ref
            and instance_item.item_id.ref._name == "of.zync.pipeline"
            and instance_item.item_id.ref._has_done_pipeline(instance_item)
        ):
            zyncpipelines.append((None, instance_item))
        else:
            for conn, item in instance_item.walk_to_start(prev_conn=self):
                if (
                    item.item_id.ref
                    and item.item_id.ref._name == "of.zync.pipeline"
                    and item.item_id.ref._has_done_pipeline(item)
                ):
                    inst_item = instance_item._get_wk_instance_item(
                        instance_item.instance_id, item.item_id
                    )
                    zyncpipelines.append((conn, inst_item))

        if len(zyncpipelines) > 1:
            raise NotImplementedError("Too many previous pipelines found.")
        if zyncpipelines:
            conn, item = zyncpipelines[0]
            metadata = item.restore_metadata()
            zbinstance = self.env["zbs.instance"].sudo().browse(metadata["instance_id"])
            if zbinstance.state == "success":
                records = zbinstance._eval_data()
                if conn and conn._evals_zync_record:
                    filtered_records = self._filter_records(
                        instance_item,
                        records,
                    )
                    return filtered_records
                return records
            else:
                raise Exception("ZB Pipeline is not finished: {zbinstance.id}")
        return []

    def _filter_records(self, instance_item, records, stop_on_match=False):
        objs = self._get_eval_objects(instance_item)
        res = []
        records = self.env["zebrooset"].rs(records)
        for index, record in records.iterate_data(records):
            objs["zync_record"] = record
            objs["record"] = record
            if self._eval(self.condition, **objs):
                res.append(record)
                if stop_on_match:
                    break
        return res

    def _zbs_get_previous_data(self, instance_item):
        return self._retrieve_zync_records(instance_item)
