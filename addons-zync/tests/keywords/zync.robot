*** Settings ***
Documentation       Tools for robot tests

Library             OperatingSystem
Library             ../../addons_robot/robot_utils/library/default_vars.py
Resource            ../../addons_robot/robot_utils/keywords/odoo.robot
Resource            ../../addons_robot/robot_utils/keywords/tools.robot
Resource            ../../addons_robot/robot_utils/keywords/wodoo.robot
Resource            ../../addons_robot/robot_utils/keywords/test_setup.robot


*** Keywords ***
Setup Test
    Log To Console   Setting up Test
    Setup Test Basic
    Ensure Environment Variables
    Login

Teardown Test
	# | FAIL |
    # Teardown failed:
    # InvalidSessionIdException: Message: Cannot find session with id: a44f19129f1935559252e135370eb93c
    # --> so i added Run Keyword And Ignore Error
    Run Keyword And Ignore Error  Close All Browsers

Ensure Environment Variables
    ${RUN_ODOO_QUEUEJOBS}=    Get Environment Variable    RUN_ODOO_QUEUEJOBS
    ${RUN_ODOO_CRONJOBS}=    Get Environment Variable    RUN_ODOO_CRONJOBS
    ${ODOO_QUEUEJOBS_CRON_IN_ONE_CONTAINER}=    Get Environment Variable    ODOO_QUEUEJOBS_CRON_IN_ONE_CONTAINER
    ${ODOO_CRON_IN_ONE_CONTAINER}=    Get Environment Variable    ODOO_CRON_IN_ONE_CONTAINER

    Should Be Equal As Strings    ${RUN_ODOO_QUEUEJOBS}    1
    Should Be Equal As Strings    ${RUN_ODOO_CRONJOBS}    1
    Should Be Equal As Strings    ${ODOO_QUEUEJOBS_CRON_IN_ONE_CONTAINER}    0
    Should Be Equal As Strings    ${ODOO_CRON_IN_ONE_CONTAINER}    0

Setup Access To Zync

Goto Zync
    Screenshot
    MainMenu    zbsync.root_menu
    Wait Until Element Is Visible    xpath=//a[text() = 'Zebroo Sync' and @role = 'menuitem']

Import Pipeline    [Arguments]    ${newname}    ${pipeline_path}
    Goto Zync
    ClickMenu    zbsync.menu_pipelines
    Screenshot
    ClickMenu    zbsync_xport_ui.menu_import_pipeline
    Wait Until Page Contains Element  css=div[name='filecontent']
    Odoo Upload File    filecontent    ${pipeline_path}
    Write    newname    ${newname}
    Odoo Command    kill odoo_cronjobs odoo_queuejobs    # cronjob cannot me modified right now came
    Wait To Click    css=button[name='ok']
    Wait Until Element Is Visible    css=button[name="add_worker"]
    ${id}=    Get Instance ID From Url    zbs.pipeline
    Screenshot
    Odoo Command    up -d odoo_cronjobs odoo_queuejobs
    RETURN    ${id}

Zync New UI Button    [Arguments]    ${caption}    ${pipeline_id}    ${model}    ${viewname}
    Goto Zync
    Screenshot
    ClickMenu    zbsync_uibinding.menu_root
    ClickMenu    zbsync_uibinding.menu_buttons
    Screenshot
    Wait To Click    css=button.o_list_button_add  position=1
    Write    model_id    ${model}
    Write    pipeline_id    ${pipeline_id}
    Write    view_ids    ${viewname}
    Write    caption    ${caption}
    ${buttons}=    Odoo Search    zbs.pipeline.button    []    limit=1    order=id desc
    Form Save
    Wait To Click    css=button[name='update_form_action']
    ${buttons2}=    Odoo Search    zbs.pipeline.button    [('pipeline_id.name','ilike', '${TOKEN}')]    limit=1    order=id desc
    IF    ${buttons}
        Assert    ${buttons2}[0] == 1 + ${buttons}[0]    There must be a new button (A)
    ELSE
        Assert    len(${buttons2}) == 1    There must be a new button (B)
    END
    ${button_record}=    Odoo Read Field    zbs.pipeline.button    ${buttons2}    model_id
    Assert    bool(${button_record})    # many2one field is (85, 'Contact')
    Assert    '${button_record}[1]' == 'Contact'    Model ID should be set by many2one field
    Screenshot

Zync Complete Run    [Arguments]    ${instance_id}
    # call with:
    # Wait Until Keyword Succeeds    10x    500ms    Run Keyword    Zync Run Instance Done
    ${no_cron_start}=    Odoo Read Field    zbs.instance    ${instance_id}    no_cron_start
    ${step_by_step_mode}=    Odoo Read Field    zbs.instance    ${instance_id}    test_mode
    Log To Console    Complete Run Zync of instance-id ${instance_id}
    WHILE    ${TRUE}
        TRY
            IF    ${no_cron_start}
                Odoo Execute    zbs.instance    ids=${instance_id}    method=heartbeat_ui
            ELSE
                Zync Run Cron Pipeline Pusher
                Sleep    1s
            END
        EXCEPT
            Log To Console    Exception in Zync Run Cron Pipeline Pusher: ${ERROR}
            Log To Console    Ignoring and retrying
            Sleep    0.2s
        END
        ${state}=    Odoo Read Field    zbs.instance    ${instance_id}    state
        Log To Console    Instance ${instance_id} is in state ${state}
        IF    '${state}' in ${{['success', 'failed']}}    BREAK
    END
    IF    '${state}' in ${{['failed']}}    FAIL  Zync Instance ${instance_id} failed


Zync Run Cron Pipeline Pusher
    ${cron_ids}=    Odoo Search    ir.cron    ['|', ('active','=', True), ('active','=',False), ('name', '=', 'zbs_pipeline_pusher')]
    Assert    len(${cron_ids}) == 1
    # Task could be executed at the moment
    Wait Until Keyword Succeeds    120x    1s  Odoo Execute    ir.cron    ids=${cron_ids[0]}    method=method_direct_trigger

Zync Add Worker    [Arguments]    ${worker}
    # needs form of pipeline be open
    Wait To Click    button[name='add_worker']
    Write    model_id    ${worker}
    Wait To Click    button[name='ok']
    ${locator_button_worker}=    CSS Identifier With Text    div button  ${worker}  match=contains
    Wait Until Element is Visible    css=${locator_button_worker}
    Capture Page Screenshot

    # Open in Form view
    Wait To Click    ${locator_button_worker}
    Capture Page Screenshot
