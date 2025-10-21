*** Settings ***
Documentation       Simple Pipeline Testing

Library             OperatingSystem
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
${SNIPPET_MODE}         ${{ 0 }}
@{INSTALL_MODULES}      robot_utils    zbsync
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Create a pipeline
    ## make csv file
    Goto Zync
    Wait To Click    button.btn.btn-primary.o_list_button_add    position=1  # [contains(@class, 'o_list_button_add')][1]
    Write    name    simple_pipe_test1_${TOKEN}
    FormSave

    Zync Add Worker    Demo-Data
    Write    demo_count    20
    Wait To Click    button[name='make_demo']
    Breadcrumb Back
    Zync Add Worker    Python Code Worker

    ${code}=    Set Variable    record.name

    Write    code    ${code}
    Screenshot
    FormSave
    Breadcrumb Back

    # make an instance
    Wait To Click    button[name = 'run_test']
    ${instance_id}=    Get Instance ID From Url    zbs.instance
    Screenshot
    Zync Complete Run    ${instance_id}
    Wait Until Element Is Visible    css=div.zbs-batch.success
    Screenshot

    Breadcrumb Back
    Goto View    zbs.instance    ${instance_id}    form
    ${success_batches}=    GetWebelements    css=div.zbs-batch.success
    ${len_success_batches}=    Get Length    ${success_batches}
    Should Be Equal As Strings    '${len_success_batches}'    '4'
