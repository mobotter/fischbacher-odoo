*** Comments ***
# odoo-require: zbsync,robot_utils


*** Settings ***
Documentation       Simple Pipeline Testing

Library             OperatingSystem
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
${SNIPPET_MODE}         0
@{INSTALL_MODULES}      robot_utils    zbsync
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Let cronjob create an instance
    ## make csv file

    Goto Zync
    Screenshot
    Wait To Click    button.btn.btn-primary.o_list_button_add   position=1  tooltip=Creates a new pipeline
    Write    name    test cronjobs created and executed ${TOKEN}
    FormSave

    Zync Add Worker    Demo-Data
    Write    demo_count    20
    Wait To Click    button[name='make_demo']
    Screenshot

    # make an instance
    Breadcrumb Back

    Odoo Button    name=cronjobs
    ${css_modal_dialog}=    Set Variable    div.modal-dialog
    ${css}=    CSS Identifier With Text    [name='cronjob_ids'] a    Add a line
    Wait To Click    css=${css}

    ${css}=    CSS Identifier With Text    ${css_modal_dialog} button    New
    Wait To Click  css=${css}
    ${css_modal_dialog}=    Set Variable    div.modal-dialog
    ${css}=    CSS Identifier With Text    ${css_modal_dialog} div[name='cronjob_ids'] a    Add a line
    Wait To Click    ${css}
    Write    name    per minute    css_parent=${css_modal_dialog}
    ${css_modal_dialog}=    Set Variable    div.modal-dialog
    Write    interval_type    Minutes    parent=cronjob_ids    css_parent=${css_modal_dialog}
    Wait To Click    ${css_modal_dialog} button.o_form_button_save
    Wait To Click  button.o_form_button_save
    Wait for Instance to be created


*** Keywords ***
Wait for Instance to be created
    ${started}=    Get Time    epoch
    ${timeout}=    Evaluate    140
    Odoo Start Cronjobs
    ${initial_count_instances}=    Odoo Search    zbs.instance    []    count=${TRUE}
    WHILE    ${TRUE}
        ${current_time}=    Get Now
        Log To Console
        ...    Waiting for instance to be created should happen within ${timeout} seconds. Current time is: ${current_time}
        ${end_time}=    Get Time    epoch

        ${elapsed_seconds}=    Evaluate    ${end_time} - ${started}
        IF    ${elapsed_seconds} > ${timeout}
            FAIL    Timeout ${timeout} failed. Any instance was not created.
        END

        Wait Queuejobs Done
        ${count_instances}=    Odoo Search    zbs.instance    []    count=${TRUE}
        IF    ${count_instances} > ${initial_count_instances}    BREAK
        Sleep    5s
    END
