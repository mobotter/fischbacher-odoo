*** Comments ***


*** Settings ***
Documentation       Tests lots of data to be imported

Library             OperatingSystem
Resource            ../../tests/keywords/zync.robot

Test Setup          Setup Grabber Test
Test Teardown       Teardown Test


*** Variables ***
@{INSTALL_MODULES}      robot_utils    zbsync_odoo  zbsync_xport_ui
@{UNINSTALL_MODULES}    ${NONE}

*** Test Cases ***
Grab Remote as Browsable
    Setup Pipeline  remote=${TRUE}  format=Browsable Object

Grab Remote as JSON
    Setup Pipeline  remote=${TRUE}  format=JSON

Grab Local as Browsable
    Setup Pipeline  remote=${FALSE}  format=Browsable Object

Grab Local as JSON
    Setup Pipeline  remote=${FALSE}  format=JSON

*** Keywords ***
Setup Grabber Test
	Setup Test
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
    Odoo Search Unlink  zbs.test.order  []
	Odoo Create  zbs.test.order  ${{ {'name': 'order1'} }}

Setup Pipeline  [Arguments]  ${remote}=${NONE}  ${format}=${NONE}
	Goto Zync

    Wait To Click    button.btn.btn-primary.o_list_button_add    tooltip=Creates a new pipeline
    Write    name    Test Remote=${remote} format=${format} ${TOKEN}
    FormSave

    Zync Add Worker    Odoo Grabber
	IF  ${remote}
		Write   connection_id  odoo fake remote
	ELSE
		Write   connection_id  Local Odoo
	END
	Write  model  zbs.test.order
	Write  odoo_as  ${format}
	IF  '${format}' == 'JSON'
		Write  fields_to_read  name
	END
	Breadcrumb Back

    Zync Add Worker    Python Code Worker
	${code}=  Catenate  SEPARATOR=\n  assert record  assert record.name == 'order1'  True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}