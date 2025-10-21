*** Comments ***


*** Settings ***
Documentation       Tests lots of data to be imported

Library             OperatingSystem
Resource            ../../tests/keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test

*** Variables ***
@{INSTALL_MODULES}      robot_utils    zbsync_odoo  zbsync_xport_ui
@{UNINSTALL_MODULES}    ${NONE}

*** Test Cases ***
1006 many2many local
	Dumper Cleanup 1006 many2many
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1006 many2many  remote=${remote}  prev_instance_id=${instance_id}


1006 many2many remote
	Dumper Cleanup 1006 many2many
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1006 many2many  remote=${remote}

*** Keywords ***
Dumper Core 1006 many2many  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1006-many2many-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  env["zbs.test.tag"].create(  [  {"name": "tag1"},  ]  )   res = {  "name": "order1",  "___keys": ["name"],  "tag_ids": [{"name": "tag1", "anyfield": "v1", "___keys": ["name"]}],  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.created.id)  assert record.name == "order1"  assert record.tag_ids.name == "tag1"  assert record.tag_ids.anyfield == "v1"  assert record.tag_ids.search_count([]) == 1  assert isinstance(data.created[0].id, int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1006 many2many
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Test Cases ***
1007 many2many update m2m local
	Dumper Cleanup 1007 many2many update m2m
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	# preparation steps
	${instance_id}=  Dumper Core 1006 many2many  remote=${remote}  prev_instance_id=${instance_id}
	Dumper Core 1007 many2many update m2m  remote=${remote}  prev_instance_id=${instance_id}


1007 many2many update m2m remote
	Dumper Cleanup 1007 many2many update m2m
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	# preparation steps
	${instance_id}=  Dumper Core 1006 many2many  remote=${remote}  prev_instance_id=${instance_id}
	Dumper Core 1007 many2many update m2m  remote=${remote}

*** Keywords ***
Dumper Core 1007 many2many update m2m  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1007-many2many update m2m-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}     res = data = {  "name": "order1",  "___keys": ["name"],  "tag_ids": [{"name": "tag2", "anyfield": "v2", "___keys": ["name"]}],  }  data    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record.name == "order1"  assert "tag1" in record.tag_ids.mapped("name")  assert "tag2" in record.tag_ids.mapped("name")  assert "v1" in record.tag_ids.mapped("anyfield")  assert "v2" in record.tag_ids.mapped("anyfield")  assert record.tag_ids.search_count([]) == 2    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1007 many2many update m2m
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Test Cases ***
1008 many2many test delete local
	Dumper Cleanup 1008 many2many test delete
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	# preparation steps
	${instance_id}=  Dumper Core 1006 many2many  remote=${remote}  prev_instance_id=${instance_id}
	${instance_id}=  Dumper Core 1007 many2many update m2m  remote=${remote}  prev_instance_id=${instance_id}
	Dumper Core 1008 many2many test delete  remote=${remote}  prev_instance_id=${instance_id}


1008 many2many test delete remote
	Dumper Cleanup 1008 many2many test delete
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	# preparation steps
	${instance_id}=  Dumper Core 1006 many2many  remote=${remote}  prev_instance_id=${instance_id}
	${instance_id}=  Dumper Core 1007 many2many update m2m  remote=${remote}  prev_instance_id=${instance_id}
	Dumper Core 1008 many2many test delete  remote=${remote}

*** Keywords ***
Dumper Core 1008 many2many test delete  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1008-many2many test delete-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}     res = data = {  "name": "order1",  "___keys": ["name"],  "___keys_delete": ["tag_ids"],  "tag_ids": [{"name": "tag1", "___keys": ["name"]}],  }  data    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record.name == "order1"  assert "tag1" in record.tag_ids.mapped("name")  assert "tag2" not in record.tag_ids.mapped("name")  assert "v1" in record.tag_ids.mapped("anyfield")  assert "v2" not in record.tag_ids.mapped("anyfield")  assert record.tag_ids.search_count([]) == 2    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1008 many2many test delete
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []

*** Keywords ***
#Keywords from previous files
*** Keywords ***
Dumper Core 1000 m2o_with_id  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1000-m2o_with_id-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  partner1 = env['zbs.test.partner'].create({"name": "hans"})   res = {  "name": "testpartner1",  "partner_id": partner1.id,  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record.created.name == "testpartner1"  assert record.created.partner_id  assert env['zbs.test.partner'].browse(record.created.partner_id).name == "hans"  assert bool(isinstance(data.created[0].id, int))    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1000 m2o_with_id
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1001 m2o_keyresolve  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1001-m2o_keyresolve-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  partner1 = env['zbs.test.partner'].create({"name": "hans"})   res = {  "name": "testpartner1",  "partner_id": {  "___keys": ["name"],  "name": "hans",  },  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  assert record.created.name == "testpartner1"  partner = env['zbs.test.partner'].browse(record.created.partner_id)  assert partner.name == "hans"  assert partner.search_count([]) == 1  assert isinstance(data.created[0].id, int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1001 m2o_keyresolve
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1002 m2o_keyresolve_two_levels_recursive  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1002-m2o_keyresolve_two_levels_recursive-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  env["zbs.test.order"].search([]).unlink()  env["zbs.test.partner"].search([]).unlink()  partner1 = env["zbs.test.partner"].create({"name": "hans"})   res = {  "name": "testpartner1",  "partner_id": {  "___keys": ["name"],  "name": "hans",  "parent_partner_id": {  "___keys": ["name"],  "name": "hans",  },  },  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  order = env['zbs.test.order'].browse(record.created.id)  assert order.name == "testpartner1"  partner = env['zbs.test.partner'].browse(record.created.partner_id)  assert partner.name == "hans"  assert partner.search_count([]) == 1  assert(isinstance(data.created[0].id, int))    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1002 m2o_keyresolve_two_levels_recursive
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1003 one2many  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1003-one2many-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  env["zbs.test.order.line"].search([]).unlink()  env["zbs.test.order.line"].create(  [  {"name": "product1"},  {"name": "product2"},  ]  )   res = {  "name": "order1",  "line_ids": [  {"name": "product1", "___keys": ["name"]},  {"name": "product2", "___keys": ["name"]},  ],  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.created.id)  assert record.name == "order1"  assert record.line_ids[0].name == "product1"  assert record.line_ids[1].name == "product2"  assert isinstance(data.created[0].id, int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1003 one2many
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1004 one2many with extra non key fields  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1004-one2many with extra non key fields-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}     res = {  "name": "order1",  "___keys": ["name"],  "line_ids": [  {"name": "product1", "___keys": ["name"], "anyfield": "abc"},  ],  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record.name == "order1", 'order1 name not found'  assert record.line_ids[0].name == "product1", 'product should be product1'  assert record.line_ids[0].anyfield == "abc", 'anyfield should be abc'  assert len(record.line_ids) == 2, 'lines should be 2'    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1004 one2many with extra non key fields
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1005 one2many_unlink  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1005-one2many_unlink-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}     res = {  "name": "order1",  "___keys": ["name"],  "___keys_delete": ["line_ids"],  "line_ids": [  {  "name": "product1",  "anyfield": "abcd",  "___keys": ["name"],  },  ],  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.order
	Write   only_new_values  ${TRUE}
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Form Save
	Breadcrumb Back

	# set python worker for checking
	Odoo Button  text=Python Code Worker-0-Check Dumper
	${code}=  Catenate  SEPARATOR=\n  assert record  order = env['zbs.test.order'].browse(record.updated[0][0])  assert order.name == "order1", 'name should be order1'  assert order.line_ids[0].name == "product1", 'name line should be product1'  assert order.line_ids[0].anyfield == "abcd", 'name anyfield should be abcd'  assert len(order.line_ids) == 1    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1005 one2many_unlink
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []