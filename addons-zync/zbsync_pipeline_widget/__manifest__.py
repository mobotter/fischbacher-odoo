{
    "name": "zbsync_pipeline_widget",
    "version": "1.0",
    "author": "Zebroo GmbH (hello@zebroo.de)",
    "depends": ["zbsync"],
    "data": ["views/instance.xml", "views/pipeline.xml"],
    "external_dependencies": {"python": [], "bin": []},
    "assets": {
        "web.assets_backend": [
            "zbsync_pipeline_widget/static/src/css/pipelinerenderer.scss",
            "zbsync_pipeline_widget/static/src/js/batch.js",
            "zbsync_pipeline_widget/static/src/js/pausebutton.js",
            "zbsync_pipeline_widget/static/src/js/pipelineinstance_renderer.js",
            "zbsync_pipeline_widget/static/src/js/pipelinerenderer.js",
            "zbsync_pipeline_widget/static/src/js/stringinput.js",
            "zbsync_pipeline_widget/static/src/js/updateline.js",
            "zbsync_pipeline_widget/static/src/xml/pipeline_1_renderer.xml",
            "zbsync_pipeline_widget/static/src/xml/pipeline_2_instance_renderer.xml",
        ]
    },
    "demo": [],
    "test": [],
    "application": False,
    "web": True,
    "license": "Other proprietary",
}
