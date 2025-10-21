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
1021 many2many with odoo records unlink local
	Dumper Cleanup 1021 many2many with odoo records unlink
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	# preparation steps
	${instance_id}=  Dumper Core 1019 many2many with odoo records  remote=${remote}  prev_instance_id=${instance_id}
	${instance_id}=  Dumper Core 1020 many2many with odoo records update  remote=${remote}  prev_instance_id=${instance_id}
	Dumper Core 1021 many2many with odoo records unlink  remote=${remote}  prev_instance_id=${instance_id}


1021 many2many with odoo records unlink remote
	Dumper Cleanup 1021 many2many with odoo records unlink
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	# preparation steps
	${instance_id}=  Dumper Core 1019 many2many with odoo records  remote=${remote}  prev_instance_id=${instance_id}
	${instance_id}=  Dumper Core 1020 many2many with odoo records update  remote=${remote}  prev_instance_id=${instance_id}
	Dumper Core 1021 many2many with odoo records unlink  remote=${remote}

*** Keywords ***
Dumper Core 1021 many2many with odoo records unlink  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1021-many2many with odoo records unlink-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  tag1 = env['zbs.test.tag'].search([('name', '=', 'tag1')]).ensure_one()  tag2 = env['zbs.test.tag'].search([('name', '=', 'tag2')]).ensure_one()   res = {  "name": "order1",  "___keys": ["name"],  "___keys_delete": ["tag_ids"],  "tag_ids": [  {  "_type": "odoo_recordset",  "model": tag1._name,  "ids": tag1.ids,  "uid": env.uid,  "su": False,  "context": {},  },  ],  }    res  
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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record.name == "order1"  assert "tag1" in record.tag_ids.mapped("name")  assert "tag2" not in record.tag_ids.mapped("name")  assert record.tag_ids.search_count([]) == 2    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1021 many2many with odoo records unlink
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Test Cases ***
1022 field dot separated local
	Dumper Cleanup 1022 field dot separated
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1022 field dot separated  remote=${remote}  prev_instance_id=${instance_id}


1022 field dot separated remote
	Dumper Cleanup 1022 field dot separated
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1022 field dot separated  remote=${remote}

*** Keywords ***
Dumper Core 1022 field dot separated  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1022-field dot separated-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  partner1 = env["zbs.test.partner"].create({"name": "field_dot_separated"})  order = env["zbs.test.order"].create(  {"name": "test-order", "partner_id": partner1.id}  )   res = {  "id": order.id,  "partner_id.name": "francesco",  "___keys": [  "id",  ],  }    res  
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
	${code}=  Catenate  SEPARATOR=\n  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record  assert record.name == "test-order"  assert record.partner_id.name == "francesco"    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1022 field dot separated
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Test Cases ***
1023 do not updated write_date of tag when adding tag to partner local
	Dumper Cleanup 1023 do not updated write_date of tag when adding tag to partner
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1023 do not updated write_date of tag when adding tag to partner  remote=${remote}  prev_instance_id=${instance_id}


1023 do not updated write_date of tag when adding tag to partner remote
	Dumper Cleanup 1023 do not updated write_date of tag when adding tag to partner
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1023 do not updated write_date of tag when adding tag to partner  remote=${remote}

*** Keywords ***
Dumper Core 1023 do not updated write_date of tag when adding tag to partner  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1023-do not updated write_date of tag when adding tag to partner-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  tag = env['zbs.test.tag'].create({'name': 'tag1', 'anyfield': 'somevalue'})  partner1 = env["zbs.test.partner"].create({"name": "partner1"})  instance_env['tag_write_date'] = tag.write_date   res = {  "id": partner1.id,  "tag_ids": [  {  "___keys": ["name"],  "name": "tag1",  }  ],  "___keys": [  "id",  ],  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.partner
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
	${code}=  Catenate  SEPARATOR=\n  partner = env['zbs.test.order'].browse(record.updated[0][0])  tag = env['zbs.test.tag'].search([('name', '=', 'tag1')])  assert tag.write_date == instance_env['tag_write_date'], f"Write date of tag should not change: {tag.write_date} {instance_env['tag_write_date']}"  assert tag.anyfield == "somevalue", f"Tag should have anyfield value not {tag.anyfield}"    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1023 do not updated write_date of tag when adding tag to partner
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
Dumper Core 1009 default_value_and_filter_data_to_delta  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1009-default_value_and_filter_data_to_delta-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

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

Dumper Cleanup 1009 default_value_and_filter_data_to_delta
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1010 default value  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1010-default value-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  env['zbs.test.tag'].search([]).unlink()  env["zbs.test.tag"].create(  [  {"name": "tag1", "anyfield": "v1"},  ]  )   res = {  "name": "tag1",  "anyfield": "v2",  "___default_values": ["anyfield"],  "___keys": ["name"],  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.tag
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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.tag'].browse(record.updated[0][0])  assert record.name == "tag1"  assert record.anyfield == "v1"  assert isinstance(data.updated[0][0], int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1010 default value
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1011 delta values  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1011-delta values-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  env["zbs.test.tag"].search([]).unlink()  env["zbs.test.tag"].create(  [  {"name": "tag1", "anyfield": "v1"},  ]  )   res = {  "name": "tag1",  "anyfield": "v2",  "___filter_to_delta": True,  "___keys": ["name"],  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.tag
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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.tag'].browse(record.updated[0][0])  assert record.name == "tag1", "tag name should be tag1"  assert record.anyfield == "v2", "anyfield should be v2"  assert isinstance(data.updated[0][0], int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1011 delta values
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1012 if idcolumn set  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1012-if idcolumn set-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  tag = env["zbs.test.tag"].create(  [  {"name": "tag1", "anyfield": "v1"},  ]  )   res = {  "name": "tag2",  "id": tag.id,  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.tag
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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.tag'].browse(record.updated[0][0])  assert record.name == "tag2"  assert record.anyfield == "v1"  assert isinstance(data.updated[0][0], int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1012 if idcolumn set
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1013 many2one  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1013-many2one-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}     res = {  "name": "order1",  "line_ids": [  {"name": "product1", "___keys": ["name"]},  {"name": "product2", "___keys": ["name"]},  ],  }    res  
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

Dumper Cleanup 1013 many2one
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1014 many2one update  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1014-many2one update-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record.name == "order1"  assert record.line_ids[0].name == "product1"  assert record.line_ids[0].anyfield == "abc"  assert len(record.line_ids) == 2  prev_instance_env = env["zebrooset"].loads(env['zbs.instance'].browse(instance_env.prev_instance_id).environment or '{}')    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1014 many2one update
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1015 many2one test unlink  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1015-many2one test unlink-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record.name == "order1"  assert record.line_ids[0].name == "product1"  assert record.line_ids[0].anyfield == "abcd"  assert len(record.line_ids) == 1    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1015 many2one test unlink
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1016 many2one no keys  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1016-many2one no keys-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}     res = [{"name": "hans", "parent_partner_id": "meike"}]    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.partner
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
	${code}=  Catenate  SEPARATOR=\n  record = env['zbs.test.partner'].search([]).filtered(lambda r: r.name == "hans")  assert len(record) == 1  assert record  assert record.name == "hans"  assert record.parent_partner_id.name == "meike"  assert isinstance(data.created[0].id, int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1016 many2one no keys
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1017 many2one no keys 2  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1017-many2one no keys 2-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}     res = {  "name": "hans2",  "parent_partner_id": "meike",  }    res  
	${worker_const_id}=  Get Instance Id From Url  zbs.transformer.python
	${data}=   Create Dictionary  code=${data}
	Odoo Write   zbs.transformer.python  ${worker_const_id}  ${data}
	Breadcrumb Back


	# set dumper model and connection
	Odoo Button  text=Odoo Dumper-0-Check Dumper
	Write   model  zbs.test.partner
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
	${code}=  Catenate  SEPARATOR=\n  record = env['zbs.test.partner'].search([]).filtered(lambda r: r.name == "hans2")  assert len(record) == 1  assert record  assert record.name == "hans2"  assert record.parent_partner_id.name == "meike"    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1017 many2one no keys 2
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1018 many2many_just_ids  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1018-many2many_just_ids-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  env['zbs.test.tag'].search([]).unlink()  tag1 = env["zbs.test.tag"].create(  [  {"name": "tag1"},  ]  )   res = {  "name": "order1",  "___keys": ["name"],  "tag_ids": [tag1.id],  }    res  
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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.created.id)  assert record.name == "order1"  assert record.tag_ids.name == "tag1"  assert record.tag_ids.search_count([]) == 1  assert isinstance(data.created[0].id, int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1018 many2many_just_ids
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1019 many2many with odoo records  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1019-many2many with odoo records-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  tag1 = env["zbs.test.tag"].create({"name": "tag1"})  tag2 = env["zbs.test.tag"].create({"name": "tag2"})   res = {  "name": "order1",  "___keys": ["name"],  "tag_ids": [  {  "_type": "odoo_recordset",  "model": tag1._name,  "ids": tag1.ids,  "uid": env.uid,  "su": False,  "context": {},  },  ],  }    res  
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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.created.id)  assert record.name == "order1"  assert record.tag_ids.name == "tag1"  assert record.tag_ids.search_count([]) == 2  assert isinstance(data.created[0].id, int)    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1019 many2many with odoo records
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []
*** Keywords ***
Dumper Core 1020 many2many with odoo records update  [Arguments]  ${remote}=${NONE}  ${prev_instance_id}=${FALSE}
	Goto Zync
	${pipe}=    Import Pipeline    1020-many2many with odoo records update-${TOKEN}    ${SUITE_PATH}/pipeline.dumper.json

	Odoo Button  text=Python Code Prepare DataDumper

	${data}=     Catenate  SEPARATOR=\n  instance_env.prev_instance_id=${prev_instance_id}  tag1 = env['zbs.test.tag'].search([('name', '=', 'tag1')]).ensure_one()  tag2 = env['zbs.test.tag'].search([('name', '=', 'tag2')]).ensure_one()   res = {  "name": "order1",  "___keys": ["name"],  "tag_ids": [  {  "_type": "odoo_recordset",  "model": tag1._name,  "ids": tag1.ids + tag2.ids,  "uid": env.uid,  "su": False,  "context": {},  }  ],  }    res  
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
	${code}=  Catenate  SEPARATOR=\n  assert record  record = env['zbs.test.order'].browse(record.updated[0][0])  assert record.name == "order1"  assert "tag1" in record.tag_ids.mapped("name")  assert "tag2" in record.tag_ids.mapped("name")  assert record.tag_ids.search_count([]) == 2    True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}

	RETURN  ${instance_id}

Dumper Cleanup 1020 many2many with odoo records update
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
	Odoo Search Unlink    zbs.test.partner    []
	Odoo Search Unlink    zbs.test.order    []
	Odoo Search Unlink    zbs.test.order.line    []
	Odoo Search Unlink    zbs.test.tag  []