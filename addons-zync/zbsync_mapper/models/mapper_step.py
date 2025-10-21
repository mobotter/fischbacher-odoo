# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import _, fields, models, tools
from datetime import datetime
import logging

logger = logging.getLogger("zbsync.mapper.step")


class ZBSMapperStep(models.Model):
    _inherit = "zbs.worker"
    _name = "zbs.mapper"
    _description = "Zync Mapper"

    mapping_direction = fields.Selection(
        [
            ("import", "Import to Local Odoo"),
            ("export", "Export to external Model"),
            ("transfer", "transfer"),
        ]
    )
    can_keys = fields.Boolean("Can Keys", tracking=True, default=True)
    mapping_ids = fields.One2many(
        "zbs.mapping",
        "step_id",
        string="Mappings",
        tracking=True,
        xport_ignore=True,
        context={"active_test": False},
        copy=False,  # done manually in copy method
    )
    # needed for export
    direct_child_mapping_ids = fields.One2many(
        "zbs.mapping",
        "step_id",
        copy=False,
        domain=[("parent_id", "=", False)],
    )
    no_metadata = fields.Boolean("No Metadata", tracking=True, default=False)

    def copy(self, default=None):
        default = default or {}
        default["mapping_ids"] = []
        res = super().copy(default)
        for map in self.mapping_ids.filtered(lambda x: not x.parent_id):
            map2 = map.with_context(default_step_id=res.id).copy({"step_id": res.id})
            assert map2.step_id == res

        return res

    def _compute_can_open_worker_detail(self):
        for rec in self:
            rec.can_open_worker_detail = False

    # @tools.ormcache("self.id")
    # brings errors: example 'if self.skip_if'
    def root_mapping_ids(self):
        self.ensure_one()
        return self.mapping_ids.filtered(lambda x: not x.parent_id and x.active)

    def process_record(self, instance, index, record, data, errors=None):
        logger.debug(f"Mapper process record index: {index}")
        mapped = self._apply_root_mappings(record)
        return mapped

    def _apply_root_mappings(self, record):
        mapped = {}
        performance = {}
        for mapping in self.root_mapping_ids():
            mapping = mapping.with_context(current_mapper=self)
            start = datetime.now()
            mapping.apply(record, mapped)
            end = datetime.now()
            elapsed = (end - start).total_seconds()
            performance[mapping] = elapsed

        for mapping, elapsed in performance.items():
            logger.debug(f"Performance mapping {mapping.id}: {elapsed}s")
        sumelapsed = sum(list(performance.values()))
        logger.debug(f"1000 records to map would take: {sumelapsed * 1000}s")

        return mapped

    def process(self, instance, data, errors=None):
        self.env["zbs.tools"].do_clear_cache(
            obj=self.mapping_ids,
            function_name="_apply_lookup_search_cached",
        )
        if not self._has_internal_loops():
            return super().process(instance, data, errors=errors)

        # TODO provide instance env or so
        self = self.with_context(
            mapper_process_initial_instance=instance,
            mapper_process_initial_data=data,
        )
        start_record = self.env["zebrooset"].rs({})
        res = self._apply_root_mappings(start_record)
        res = instance.Result(res)
        return res

    def get_records_for_apply(self, myfunc):
        instance = self.env.context.get("mapper_process_initial_instance")
        data = self.env.context.get("mapper_process_initial_data")
        return self._process_worker_base(instance, data, func=myfunc, errors=None)

    @tools.ormcache("self.id")
    def _has_internal_loops(self):
        return bool(self.mapping_ids.filtered(lambda x: x.loop_records))

    def _apply_keep_input_merge_record(self, rec, kept):
        rec["___kept_input"] = kept

    def open_list_action(self):
        self.ensure_one()
        return {
            "name": _("Mapping"),
            "view_type": "form",
            "view_mode": "form",
            "context": {
                "default_step_id": self.id,
                "active_test": False,
                "zbs_instance": self.env.context.get("zbs_instance"),
            },
            "res_model": "zbs.mapping",
            "domain": [("step_id", "=", self.id)],
            "views": [(False, "list")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def _compute_can_open_worker_detail(self):
        for rec in self:
            rec.can_open_worker_detail = False

    def open(self):
        return {
            "view_type": "form",
            "res_model": self._name,
            "res_id": self.id,
            "views": [(False, "form")],
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def action_open_create_mapping_wizard(self):
        self.ensure_one()

        view = self.env.ref("zbsync_mapper.create_mapping_wizard_form")

        ctx = dict(
            default_mapper_id=self.id, default_mapping_direction=self.mapping_direction
        )

        return {
            "name": _("New Mapping for Mapper"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "zbs.create.mapping.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "context": ctx,
        }

    def delete_all_mappings(self):
        for line in self._get_pipelines():
            line.pipeline_id.snapshot()
        for mapping in self.mapping_ids:
            mapping.unlink()
