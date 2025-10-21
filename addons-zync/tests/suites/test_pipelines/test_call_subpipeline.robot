*** Settings ***
Documentation       Call subpipeline

Library             OperatingSystem
Library             SeleniumLibrary
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
${SNIPPET_MODE}         0
@{INSTALL_MODULES}      robot_utils    zbsync
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Just Run Sub Pipe
    ${main}    ${sub}=    Make pipeline main and sub    mode=${NONE}

    Goto View    zbs.pipeline    ${main}    type=form
    Wait To Click    button[name='start_from_ui_like_cronjob']
    Repeat Keyword    4 times    Zync Run Cron Pipeline Pusher

    ${len_mains}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${main})]    count=${TRUE}
    ${len_subs}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${sub})]    count=${TRUE}
    ${mains}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${main})]    state
    ${subs}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${sub})]    state

    Should Be Equal As Integers    ${len_mains}    1
    Should Be Equal As Integers    ${len_subs}    1
    Should Be Equal As Strings    ${mains[0]['state']}    success
    Should Be Equal As Strings    ${subs[0]['state']}    success

Wait Until Sub Pipe Done
    Log To Console  Before make pipeline main and sub
    ${main}    ${sub}=    Make pipeline main and sub    mode=Wait Until Done
    Log To Console  After make pipeline main and sub

    Goto View    zbs.pipeline    ${main}    type=form
    Wait To Click    button[name='run_test']
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    Log To Console  Clicked 5 times heartbeat ui

    ${len_mains}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${main})]    count=${TRUE}
    ${len_subs}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${sub})]    count=${TRUE}
    ${mains}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${main})]    state
    ${subs}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${sub})]    state
    ${main_id}=    Set Variable    ${mains[0]['id']}
    ${sub_id}=    Set Variable    ${subs[0]['id']}

    Log    Main Pipeline Should wait
    Goto View    zbs.instance    ${main_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_main}=    Odoo Read Field    zbs.instance    ${main_id}    state
    Should Be Equal As Strings    ${state_main}    running

    Log    Continue sub pipeline
    Goto View    zbs.instance    ${sub_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_sub}=    Odoo Read Field    zbs.instance    ${sub_id}    state
    Should Be Equal As Strings    ${state_sub}    success

    Log    Main Pipeline Should wait
    Goto View    zbs.instance    ${main_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_main}=    Odoo Read Field    zbs.instance    ${main_id}    state
    Should Be Equal As Strings    ${state_main}    success

Return Data from sub pipeline
    ${main}    ${sub}=    Make pipeline main and sub    mode=Return Data

    Goto View    zbs.pipeline    ${main}    type=form
    Wait To Click    button[name='run_test']
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${mains}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${main})]    state
    ${subs}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${sub})]    state
    ${main_id}=    Set Variable    ${mains[0]['id']}
    ${sub_id}=    Set Variable    ${subs[0]['id']}

    Log    Main Pipeline Should wait
    Goto View    zbs.instance    ${main_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_main}=    Odoo Read Field    zbs.instance    ${main_id}    state
    Should Be Equal As Strings    ${state_main}    running

    Log    Continue sub pipeline
    Goto View    zbs.instance    ${sub_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_sub}=    Odoo Read Field    zbs.instance    ${sub_id}    state
    Should Be Equal As Strings    ${state_sub}    success

    Log    Main Pipeline Should wait
    Goto View    zbs.instance    ${main_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_main}=    Odoo Read Field    zbs.instance    ${main_id}    state
    Should Be Equal As Strings    ${state_main}    success

    # eval data
    ${output}=    Odoo Search Read Records
    ...    zbs.instance.line.batch
    ...    [('line_id.instance_id', '=', ${sub_id})]
    ...    input_data
    ...    order=id desc
    ...    limit=1
    Should Contain    ${output[0]['input_data']}    ${TOKEN}

Fire And Forget
    ${main}    ${sub}=    Make pipeline main and sub    mode=Fire and Forget

    Goto View    zbs.pipeline    ${main}    type=form
    Wait To Click    button[name='run_test']
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${mains}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${main})]    state
    ${subs}=    Odoo Search Read Records    zbs.instance    [('pipeline_id', '=', ${sub})]    state
    ${main_id}=    Set Variable    ${mains[0]['id']}
    ${sub_id}=    Set Variable    ${subs[0]['id']}

    Log    Main Pipeline Should wait
    Goto View    zbs.instance    ${main_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_main}=    Odoo Read Field    zbs.instance    ${main_id}    state
    Should Be Equal As Strings    ${state_main}    success

    Log    Continue sub pipeline
    Goto View    zbs.instance    ${sub_id}    type=form
    Repeat Keyword    5 times    Wait To Click    button[name='heartbeat_ui']
    ${state_sub}=    Odoo Read Field    zbs.instance    ${sub_id}    state
    Should Be Equal As Strings    ${state_sub}    success

*** Keywords ***
Make Pipeline Main and Sub    [Arguments]    ${mode}
    Repeat Keyword    10 times    Zync Run Cron Pipeline Pusher
    Repeat Keyword    3    Wait Queuejobs Done

    ## make csv file
    Goto Zync

    Wait To Click    button.btn-primary.o_list_button_add  position=1  # [contains(@class, 'o_list_button_add')][1]
    Write    name    call-sub-${TOKEN}
    FormSave
    ${id_subpipeline}=    Get Instance ID From Url    zbs.pipeline

    Zync Add Worker    Python Code Worker
    Write    code    '${TOKEN}'
    FormSave
    Breadcrumb Back

    Goto Zync
    Wait To Click    button.btn.btn-primary.o_list_button_add  position=1   # [contains(@class, 'o_list_button_add')][1]
    Write    name    call-main-${TOKEN}
    FormSave
    ${id_mainpipeline}=    Get Instance ID From Url    zbs.pipeline

    Zync Add Worker    Start Other Pipeline
    ${modeset}=  Eval  bool(m)  m=${mode}
    IF    ${modeset}   Write    mode    ${mode}
    Write    pipeline_id    call-sub-${TOKEN}
    FormSave

    RETURN    ${id_mainpipeline}    ${id_subpipeline}
