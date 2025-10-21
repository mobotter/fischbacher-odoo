*** Settings ***
Documentation       Test Triggers

Library             OperatingSystem
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
${SNIPPET_MODE}         ${FALSE}
@{INSTALL_MODULES}      robot_utils    zbsync
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Test Triggers
    Odoo Search Unlink  zbs.trigger.methodhook  []
    Goto Zync
    Screenshot
    Wait To Click    button.btn.btn-primary.o_list_button_add  position=1
    Write    name    simple_pipe_test1_${TOKEN}
    FormSave
    ${pipeline_id}=    Get Instance ID From Url    zbs.pipeline

    Zync Add Worker    Demo-Data
    Write    demo_count    20
    Wait To Click    button[name='make_demo']
    Screenshot

    Breadcrumb Back
    Screenshot
    Zync Add Worker    Python Code Worker
    ${code}=    Catenate
    ...    record.name

    Screenshot

    Write    code    ${code}
    FormSave
    Screenshot
    Breadcrumb Back
    Screenshot

    # Add trigger on write
    ${model_id}=    Odoo Search    ir.model    [('model', '=', 'res.partner')]    limit=1
    ${model_id}=    Set Variable    ${{ ${model_id}[0] }}
    ${values}=    Create Dictionary
    ...    pipeline_id=${pipeline_id}
    ...    model_id=${model_id}
    ...    domain=[]
    ...    method=write
    ...    link_expression=object
    Odoo Create    zbs.trigger.methodhook    ${values}

    ${partner1}=    Odoo Search    res.partner    [('child_ids', '=', False)]    limit=1
    ${count_before}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    ${result}=    Odoo Write    res.partner    ${partner1}    ${{ {'name': 'test123'} }}
    ${count_after}=    Odoo Search    zbs.instance    [('pipeline_id', '=', ${pipeline_id})]    count=1
    Assert    ${count_before} + 1 == ${count_after}

    ${instance_id}=    Odoo Search    zbs.instance    []    order=id desc    limit=1
    ${instance_id}=    Set Variable    ${{ ${instance_id}[0] }}
    Wait Until Keyword Succeeds    10x    500ms    Run Keyword    Zync Complete Run    ${instance_id}
    Goto View    zbs.instance    ${instance_id}    form
    ${success_batches}=    GetWebelements    xpath=//div[@class='zbs-batch success']
    ${len_success_batches}=    Get Length    ${success_batches}
    Should Be Equal As Strings    '${len_success_batches}'    '4'
