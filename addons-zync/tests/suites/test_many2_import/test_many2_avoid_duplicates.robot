*** Settings ***
Documentation       Tests if per header a database can be chosen.

Library             OperatingSystem
Library             RequestsLibrary
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
@{INSTALL_MODULES}      robot_utils    zbsync    zbsync_odoo    crm
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Test Import Many2One Avoid Duplicates
    Goto Zync
    Odoo Search Unlink  model=res.partner.title  domain=[('name','=','A')]
    Odoo Search Unlink  model=res.partner  domain=[('name','=','title-%')]
    ${pipeline_id}=    Import Pipeline    import.titles.json_${TOKEN}    ${SUITE_PATH}/import.titles.json

    GoTo View  zbs.pipeline  ${pipeline_id}
    Wait To Click    button[name = 'start_from_ui_like_cronjob']
    ${instance_id}=    Get Instance ID From Url    zbs.instance
    Zync Complete Run    ${instance_id}
    Wait Queuejobs Done
    ${count}=  Odoo Search  res.partner.title  [('name','=','A')]  count=${TRUE}
    Should Be Equal As Numbers  ${count}  1  There should be exactly one title


Test the same with Many2many Records
    Goto Zync
    Odoo Search Unlink  model=res.partner.category  domain=[('name','=','A')]
    Odoo Search Unlink  model=res.partner  domain=[('name','=','title-%')]
    ${pipeline_id}=    Import Pipeline    import.categories.json_${TOKEN}    ${SUITE_PATH}/import.categories.json

    GoTo View  zbs.pipeline  ${pipeline_id}
    Wait To Click    button[name = 'start_from_ui_like_cronjob']
    ${instance_id}=    Get Instance ID From Url    zbs.instance
    Zync Complete Run    ${instance_id}
    Wait Queuejobs Done
    ${count}=  Odoo Search  res.partner.category  [('name','=','A')]  count=${TRUE}
    Should Be Equal As Numbers  ${count}  1  There should be exactly one category
