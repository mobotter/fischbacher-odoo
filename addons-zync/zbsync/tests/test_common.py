# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
import inspect
import json
import os
from odoo import models
from odoo.tests.common import TransactionCase
from odoo.tests import Form

try:
    pass
except:
    pass

import inspect
import os
from pathlib import Path

current_dir = Path(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)


class ZBSPipelineCase(TransactionCase):
    def try_nice(self, d):
        try:
            d = json.dumps(d, indent=4)
        except:
            d = str(d)
        return d

    def _get_knowledge_base_article_id(self):
        raise NotImplementedError("_get_knowledge_base_article_id")

    def output_pre(self, d):
        res = []
        res.append("<pre>")
        for line in self.try_nice(d).splitlines():
            res.append(line)
        res.append("</pre>")
        return res

    def format_setup(self, setup):
        """
        For creating nice knowledge base articles
        """
        if not getattr(self, "_testname", None):
            return
        caller = inspect.stack()[1]
        name = setup.get("name") or caller[3]
        output = []
        output.append(f"<!--{name}-->\n")
        output.append(f"<h2 name='{name}'>{name}</h2>\"")
        prev_locals = inspect.currentframe().f_back

        root_path = self._get_src_root() / self._testname
        root_path.mkdir(exist_ok=True, parents=True)

        self._format_usecases(setup, output)
        self._format_documentation(setup, output)
        self._format_sample_data(setup, output)
        self._format_expected_result(setup, output)
        self._custom_format(setup, output)

        filename = name
        for c in "?:(){}[]%$&\\ /":
            filename = filename.replace(c, "_")
        file = root_path / (filename + ".html")
        file.write_text("\n".join(output))

        setup_txt = root_path / "setup.txt"
        setup_txt.write_text(
            json.dumps({"knowledge_id": self._get_knowledge_base_article_id()})
        )

    def _format_usecases(self, setup, output):
        if not setup.get("usecase"):
            return
        output.append("<h3>Use-Cases:</h3>")
        output.append("<ul>")
        for item in setup["usecase"]:
            output.append(f"<li>{item}</li>")
        output.append("</ul>")

    def _format_documentation(self, setup, output):
        if not setup.get("documentation"):
            return
        output.append("<h3>Documentation:</h3>")
        output.append("<p>")
        output.append(setup["documentation"])
        output.append("</p>")

    def _format_sample_data(self, setup, output):
        if not setup.get("sample_data"):
            return
        output.append("<h3>Input</h3>")
        output += self.output_pre(setup["sample_data"])

    def _format_expected_result(self, setup, output):
        if not setup.get("expected_result"):
            return
        output.append("<h3>Result</h3>")
        output += self.output_pre(setup["expected_result"])

    def _get_html_output_dirname(self):
        raise NotImplementedError()

    def _get_src_root(self):
        here = current_dir
        while not (here / ".git").exists():
            here = here.parent
        res = here / "testdocs"
        res.mkdir(parents=True, exist_ok=True)
        return res

    def _custom_format(setup, output):
        raise NotImplementedError("_custom_format(self, output) missing")

    def make_simple_pipe(self, worker_class_name, worker_data):
        pipe = self.env["zbs.pipeline"].create(
            {
                "name": type(self).__name__,
            }
        )
        worker = self.env[worker_class_name].create(worker_data)
        line = self.env["zbs.pipeline.line"].create(
            {
                "pipeline_id": pipe.id,
                "sequence": 10,
                "worker_id": f"{worker._name},{worker.id}",
            }
        )
        debugger = self.env["zbs.debugger"].create(
            {
                "name": "debugger1",
            }
        )
        self.env["zbs.pipeline.line"].create(
            {
                "pipeline_id": pipe.id,
                "sequence": 10,
                "worker_id": f"{debugger._name},{debugger.id}",
            }
        )
        return pipe, line

    def add_line(self, pipeline, worker_model, vals=None):
        assert isinstance(worker_model, models.AbstractModel)
        wiz_add = Form(
            self.env["zbs.wiz.new.el"].with_context(
                active_model=pipeline._name, active_id=pipeline.id
            )
        )
        wiz_add.model_id = worker_model
        lines = self.env["zbs.pipeline.line"].search([])
        wiz_add = wiz_add.save()
        worker = wiz_add.ok()
        if vals:
            worker.write(vals)
        lines = lines.search([]) - lines
        return worker, lines
