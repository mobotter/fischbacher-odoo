/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ZBPipelineRenderer } from "./pipelinerenderer";

export class ZBPipelineInstanceRenderer extends ZBPipelineRenderer {
  static template = "zbsync.pipeline_instance_renderer";
}

registry.category("fields").add("pipeline_instance_renderer", {
  component: ZBPipelineInstanceRenderer,
  supportedTypes: ["text"],
});
