*** Settings ***
Documentation       Tests button click at instance which starts pipelines.

Library             OperatingSystem
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
@{INSTALL_MODULES}      robot_utils    zbsync    crm
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Test Pipeline With Errors
    Prepare

    Goto Zync
    ${sync_pipeline_id}=    Import Pipeline    synchron_${TOKEN}    ${SUITE PATH}/pipeline_synchron.json
    Screenshot
    ${pipelinename}=    Odoo Read Field    zbs.pipeline    ${sync_pipeline_id}    name
    Zync New UI Button    synchron    ${pipelinename}    Contact    res.partner.form
    Log To Console    1.1

    ${async_pipeline_id}=    Import Pipeline    asynchron_${TOKEN}    ${SUITE_PATH}/pipeline_asynchron.json
    Screenshot
    ${pipelinename}=    Odoo Read Field    zbs.pipeline    ${async_pipeline_id}    name
    Zync New UI Button    asynchron    ${pipelinename}    Contact    res.partner.form
    Log To Console    1.2

    # Go to a contact and click synchronous button
    MainMenu    contacts.menu_contacts
    Wait To Click    css=article.o_kanban_record    position=1
    Screenshot
    Log To Console    1.3

    # Start asynchron pipeline
    ${pipeline_id}=    Set Variable    ${async_pipeline_id}
    ${count_queuejobs}=    Odoo Search    queue.job    []    count=1
    ${count_before}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    Log To Console    ${count_before}
    ${css}=    CSS Identifier With Text    button span    text=asynchron
    Wait To Click    css=${css}
    Log To Console    1.4
    Repeat Keyword    10 times    Zync Run Cron Pipeline Pusher

    Log To Console    1.4.1
    ${count_after}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    ${count_queuejobs_after}=    Odoo Search    queue.job    []    count=1
    Assert    ${count_before} + 1 == ${count_after}
    Assert    ${count_queuejobs_after} >${count_queuejobs}
    Log To Console    1.5

    # Start synchron pipeline
    ${pipeline_id}=    Set Variable    ${sync_pipeline_id}
    ${count_queuejobs}=    Odoo Search    queue.job    []    count=1
    ${count_before}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    ${css}=    CSS Identifier With Text    button span    text=synchron
    Wait To Click    css=${css}    error_check=${FALSE}
    Sleep    2s
    Run Keyword And Expect Error    *invalid syntax*    Eval Error States
    Wait To Click    div.modal-content button.btn-primary    error_check=${False}
    Screenshot
    ${count_after}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    Assert    ${count_before} + 1 == ${count_after}    New instance should be created
    ${count_queuejobs_after}=    Odoo Search    queue.job    []    count=1
    Log    No queuejobs should be created as it is a synchronous pipeline
    Assert    ${count_queuejobs}==${count_queuejobs_after}    No new queuejobs should be created
    Log To Console    1.6

    # perhaps in future it is a nicer error message
    # Wait Until Element Is Visible    xpath=//div[contains(@class, 'o_dialog_error')]
    Log To Console    1.7
    Screenshot

Test Pipeline No Errors
    Prepare

    Log To Console    2.1

    Goto Zync
    Sleep    2s
    ${synchron_pipeline_id}=    Import Pipeline
    ...    no_error_synchron_${TOKEN}
    ...    ${SUITE_PATH}/pipeline_synchron_no_error.json
    Screenshot
    ${pipelinename}=    Odoo Read Field    zbs.pipeline    ${synchron_pipeline_id}    name
    Zync New UI Button    synchron    ${pipelinename}    Contact    res.partner.form
    Log To Console    2.2

    ${asynchron_pipeline_id}=    Import Pipeline
    ...    no_error_asynchron_${TOKEN}
    ...    ${SUITE_PATH}/pipeline_asynchron_no_error.json
    Screenshot
    ${pipelinename}=    Odoo Read Field    zbs.pipeline    ${asynchron_pipeline_id}    name
    Zync New UI Button    asynchron    ${pipelinename}    Contact    res.partner.form

    # Go to a contact and click synchronous button
    MainMenu    contacts.menu_contacts
    Wait To Click    css=article.o_kanban_record    position=1
    Screenshot
    Log To Console    2.3

    Log    Start synchron pipeline
    ${pipeline_id}=    Set Variable    ${synchron_pipeline_id}
    Screenshot
    ${count_success}=    Odoo Search
    ...    zbs.instance
    ...    [('pipeline_id', '=', ${pipeline_id}), ('state', '=', 'success')]
    ...    count=1
    ${count_queuejobs}=    Odoo Search    queue.job    []    count=1
    ${count_before}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    ${css}=    CSS Identifier With Text    button span    text=synchron
    Wait To Click    css=${css}
    Screenshot
    ${count_after}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    Assert    ${count_before} + 1 == ${count_after}
    ${count_queuejobs_after}=    Odoo Search    queue.job    []    count=1
    ${count_success_after}=    Odoo Search
    ...    zbs.instance
    ...    [('pipeline_id', '=', ${pipeline_id}), ('state', '=', 'success')]
    ...    count=1
    Log    No queuejobs should be created as it is a synchronous pipeline
    Assert    ${count_queuejobs}==${count_queuejobs_after}
    ${instance_id}=    Odoo Search
    ...    zbs.instance
    ...    [('pipeline_id', '=', ${pipeline_id})]
    ...    order=id desc
    ...    limit=1
    Assert    bool(${instance_id})
    Sleep    5s
    ${state}=    Odoo Read Field    zbs.instance    ${instance_id[0]}    state
    Should Be Equal As Strings    ${state}    success
    Log To Console    2.4

    Log    Start asynchron pipeline
    ${pipeline_id}=    Set Variable    ${asynchron_pipeline_id}
    Screenshot
    ${count_before}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    ${css}=    CSS Identifier With Text    button span    text=asynchron
    Wait To Click    css=${css}
    ${count_after}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    ${instance_id}=    Odoo Search
    ...    zbs.instance
    ...    [('pipeline_id', '=', ${pipeline_id})]
    ...    order=id desc
    ...    limit=1
    Assert    ${count_before} + 1 == ${count_after}
    Log To Console    2.5
    Wait Until Keyword Succeeds    10x    500ms    Run Keyword    Zync Complete Run    ${instance_id}
    ${state}=    Odoo Read Field    zbs.instance    ${instance_id}    state
    Should Be Equal As Strings    ${state}    success
    Log To Console    2.6

    Screenshot
    Odoo Search Unlink    zbs.pipeline.button    []


*** Keywords ***
Prepare
    Odoo Stop Queuejobs
    Odoo Search Unlink    zbs.pipeline    []
    Odoo Search Unlink    zbs.pipeline.button    []
    Odoo Search Unlink    queue.job    []

    Odoo Stop Cronjobs
    Odoo Start Queuejobs
