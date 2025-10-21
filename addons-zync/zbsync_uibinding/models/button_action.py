# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo.tools.safe_eval import safe_eval
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from lxml import etree

DEFAULT_PREFLIGHT_CHECK = """
prev_instance - the previous instance, that was started
prev_instance.state - could be 'running', 'pending', 'failed', 'success'
prev_instance_step - name of the step that failed last
obj - the current odoo object
env - env object

return True
return True, "Alright - doing it - but will take time"
return False
return False, f"Something happened at {failed_instance_step}; please check to make sure that no errors pile up"

typical:
if prev_instance.state not in ['success', 'failed']:
   return (
      False,
      f"Cannot start twice - please wait - the other instance is in state {prev_instance.state}"
   )
"""

DEFAULT_VARIABLES = """
Further variables that are available:

# sends a notification to the user
notification('text', 'success | error | warning | info', sticky=False)

# sends close window action  (not a function - is a static dict)
window_close

# combination:
notification('we did it!', 'success', sticky=False, next=window_close)

# complete sample:

notification("Success", "success", next=window_close)

"""


class ButtonAction(models.Model):
    _name = "zbs.pipeline.button"
    _description = "Zync UI Button"

    pipeline_id = fields.Many2one(
        "zbs.pipeline", string="Pipeline", ondelete="cascade", required=True
    )

    show_form_action_needs_update = fields.Boolean()
    caption = fields.Char("Caption", required=True)

    model_id = fields.Many2one("ir.model", string="Model", xport_ignore=True)
    view_ids = fields.Many2many(
        "ir.ui.view",
        string="Views",
        domain=[
            ("type", "in", ["form", "tree", "list"]),
        ],
    )
    # button_async
    preflight_check = fields.Text(help=DEFAULT_PREFLIGHT_CHECK)
    preflight_check_is_empty = fields.Boolean(
        compute="_compute_preflight_check_is_empty"
    )

    attrs_invisible = fields.Char("Attrs invisible")
    states = fields.Char("Button States")
    after_success = fields.Text(help=DEFAULT_VARIABLES)
    additional_initial_code = fields.Text()

    def unlink(self):
        for rec in self:
            rec.remove_form_action()
        res = super().unlink()
        return res

    def _check_uibinding_model(self):
        model = self.model_id.model
        if not model:
            raise UserError(_("No model found 1."))
        return model

    def update_form_action(self):
        self.remove_form_action()
        self.add_form_action()

    def add_form_action(self):
        self.remove_form_action()
        model = self._check_uibinding_model()
        button_caption = self.caption or self.name
        pipeline_id = self.id
        self.show_form_action_needs_update = False
        if not model:
            raise UserError(_("No model found 2."))
        attrs = {}
        if self.attrs_invisible:
            attrs["invisible"] = self.attrs_invisible

        def make_xml(prefix, appendix):
            xml = (
                prefix + "<button name='start_action_zbsync_from_button' "
                f"type='object' "
                ">"
                "</button>" + appendix
            )
            doc = etree.XML(xml)
            if attrs:
                doc.xpath("//button")[0].set("attrs", str(attrs))
            if self.states:
                doc.xpath("//button")[0].set("states", str(self.states))
            if button_caption:
                doc.xpath("//button")[0].set("string", str(button_caption))
            doc.xpath("//button")[0].set(
                "context",
                str(
                    {
                        "button_action_id": self.id,
                    }
                ),
            )

            xml = etree.tostring(doc)

            if not self.view_ids:
                raise ValidationError("Please provide some views!")

            for main_view in self.view_ids:
                form_name = (
                    f"pipeline-buttonaction-{model}-{pipeline_id}-{main_view.id}"
                )
                views = (
                    self.env["ir.ui.view"]
                    .sudo()
                    .search(
                        [
                            ("type", "=", "form"),
                            ("name", "=", form_name),
                        ]
                    )
                )

                if not views:
                    views = views.sudo().create(
                        {
                            "name": form_name,
                            "type": "form",
                            "arch_db": xml,
                            "model": model,
                        }
                    )
                views.sudo().write({"arch_db": xml, "inherit_id": main_view.id})

        try:
            make_xml("<header position='inside'>", "</header>")
        except ValidationError as ex:
            make_xml(
                "<xpath expr='//sheet/*[1]' position='before'><header>",
                "</header></xpath>",
            )

    def _get_default_button_view(self):
        if not self.model_id:
            return [[5]]
        model = self._check_uibinding_model()
        main_views = (
            self.env["ir.ui.view"]
            .sudo()
            .search(
                [
                    ("type", "=", "form"),
                    ("mode", "=", "primary"),
                    ("model", "=", model),
                    ("inherit_id", "=", False),
                    ("arch_db", "ilike", "<header"),
                ],
                order="priority",
            )
        )
        return main_views

    def remove_form_action(self):
        for rec in self:
            if rec.model_id:
                model = rec._check_uibinding_model()
                self.env["ir.ui.view"].sudo().search(
                    [
                        ("name", "ilike", f"pipeline-buttonaction-{model}-{rec.id}"),
                        ("model", "=", model),
                    ]
                ).unlink()

    @api.onchange("model_id")
    def _changed_model(self):
        if self.view_ids:
            return
        if not self.model_id:
            return
        self.view_ids = self._get_default_button_view()

    @api.onchange(
        "model_id",
        "view_ids",
        "states",
        "attrs_invisible",
    )
    def _changed(self):
        self.show_form_action_needs_update = True

    @api.depends("preflight_check")
    def _compute_preflight_check_is_empty(self):
        for rec in self:
            text = list(
                filter(
                    bool,
                    [
                        x
                        for x in (rec.preflight_check or "").strip().splitlines()
                        if not x.strip().startswith("#")
                    ],
                )
            )
            rec.preflight_check_is_empty = not bool(text)

    def _eval_after_success(self, obj, pipeline_instance, preflight_msg):
        code = (self.after_success or "").strip()

        action_window_close = {"type": "ir.actions.act_window_close"}

        def notification(text, type="info", sticky=False, next=None):
            res = {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "message": text,
                    "type": type,
                    "sticky": sticky,
                },
            }
            if next:
                res["params"]["next"] = next
            return res

        action = None
        if code:
            action = self.env["zbs.tools"]._exec_get_result(
                code,
                {
                    "pipeline_instance": pipeline_instance,
                    "obj": obj,
                    "window_close": action_window_close,
                    "notification": notification,
                    "preflight_msg": preflight_msg,
                },
            )
        if not action and preflight_msg:
            action = notification(preflight_msg, "success")
        return action

    @api.onchange("pipeline_id")
    def _changed_pipeline(self):
        self.caption = self.pipeline_id.name

    def _get_initial_data(self, instance):
        if not self.additional_initial_code:
            return instance
        data = safe_eval(self.additional_initial_code)
        data["obj"] = instance
        return data

    def _start(self, instance):
        # manual false so no cronjob picks it up
        pipeline = self.pipeline_id
        preflight_msg = self._preflight_check(pipeline, instance)
        initial_data = self._get_initial_data(instance)
        pipeline_instance = pipeline.start(
            initial_data,
            initiated_by="button",
        )
        pipeline_instance.button_action_model = instance._name
        pipeline_instance.button_action_id = instance.id
        pipeline_instance._roll_after_start()

        action = self._eval_after_success(instance, pipeline_instance, preflight_msg)
        return action

    def _preflight_check(self, pipeline, instance):
        if self.preflight_check_is_empty:
            return
        prev_instance = self.env["zbs.instance"].search(
            [
                ("pipeline_id", "=", pipeline.id),
                ("button_action_id", "=", instance.id),
                ("button_action_model", "=", instance._name),
            ],
            order="id desc",
            limit=1,
        )
        prev_instance_step = ""
        if prev_instance.state:
            prev_instance_step = prev_instance.next_line_id.worker_id.name
        try:
            res = self.env["zbs.tools"]._exec_get_result(
                self.preflight_check,
                {
                    "prev_instance": prev_instance,
                    "obj": instance,
                    "env": self.env,
                    "prev_instance_step": prev_instance_step,
                },
            )

            code, msg = None, ""
            if not isinstance(res, (tuple, list)):
                res = tuple([res])
            code = res[0]
            if len(res) > 1:
                msg = res[1]

            if code is True:
                return msg
            if code is False:
                raise UserError(msg or _("Pre-flight check failed."))

        except UserError:
            raise
        except Exception as e:
            raise UserError(_("Pre-flight check failed: %s") % (str(e) or repr(e)))

    def unlink(self):
        self.remove_form_action()
        return super().unlink()
