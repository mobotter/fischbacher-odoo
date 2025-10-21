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
Mapping Odoo RPC
    Setup Pipeline  remote=${TRUE}  format=Browsable Object

*** Keywords ***
Setup Grabber Test
	Setup Test
	Odoo Load Data  filepath=${SUITE_PATH}/test_setup.xml
    Odoo Search Unlink  zbs.test.order  []
    Odoo Search Unlink  zbs.test.partner  []
	${partner_id}=  Odoo Create  zbs.test.partner  ${{ {'name': 'partner1'} }}
	${TestOrder}=  Create Dictionary  name=order1  partner_id=${partner_id.id}
	Odoo Create  zbs.test.order  ${TestOrder}

Setup Pipeline  [Arguments]  ${remote}=${NONE}  ${format}=${NONE}
	Goto Zync

    Wait To Click    button.btn.btn-primary.o_list_button_add    tooltip=Creates a new pipeline
    Write    name    Test Mapping=${remote} format=${format} ${TOKEN}
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

    Zync Add Worker    Mapper
    Odoo Button  text=Table
	Odoo Button   text=Add a line
	Write  field_source  name
	Write  field_dest  ordername
	Odoo Button   text=Add a line
	Write  field_source  partner_id
	Write  field_dest  partner_id
	Breadcrumb Back

    Zync Add Worker    Python Code Worker
	${code}=  Catenate  SEPARATOR=\n  assert record  assert record.ordername == 'order1'  partner = env['zbs.test.partner'].browse(record.partner_id)  assert partner.name == 'partner1'  True
	Write   code  ${code}
	Form Save
	Breadcrumb Back

	Wait To Click    css=button[name='run_test']
	${instance_id}=  Get Instance ID From Url  zbs.instance
	Zync Complete Run  ${instance_id}
