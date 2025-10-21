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
1000 m2o_with_id local
	Dumper Cleanup 1000 m2o_with_id
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1000 m2o_with_id  remote=${remote}  prev_instance_id=${instance_id}


1000 m2o_with_id remote
	Dumper Cleanup 1000 m2o_with_id
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1000 m2o_with_id  remote=${remote}

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
*** Test Cases ***
1001 m2o_keyresolve local
	Dumper Cleanup 1001 m2o_keyresolve
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1001 m2o_keyresolve  remote=${remote}  prev_instance_id=${instance_id}


1001 m2o_keyresolve remote
	Dumper Cleanup 1001 m2o_keyresolve
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1001 m2o_keyresolve  remote=${remote}

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
*** Test Cases ***
1002 m2o_keyresolve_two_levels_recursive local
	Dumper Cleanup 1002 m2o_keyresolve_two_levels_recursive
	${remote}=  Set Variable  ${FALSE}

	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1002 m2o_keyresolve_two_levels_recursive  remote=${remote}  prev_instance_id=${instance_id}


1002 m2o_keyresolve_two_levels_recursive remote
	Dumper Cleanup 1002 m2o_keyresolve_two_levels_recursive
	${remote}=  Set Variable  ${TRUE}
	${instance_id}=  Set Variable  ${NONE}
	
	Dumper Core 1002 m2o_keyresolve_two_levels_recursive  remote=${remote}

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
#Keywords from previous files
