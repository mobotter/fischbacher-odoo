*** Comments ***
# Shows errors if tested with: odoo -f robot run test_millions.robot --repeat 50
# odoo-require: zbsync, robot_utils


*** Settings ***
Documentation       Tests lots of data to be imported

Library             OperatingSystem
Resource            ../../keywords/zync.robot
Library             ./myfaker.py

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
${DATA_FILE}    data.small/res.partner.csv
${SNIPPET_MODE}         0
@{INSTALL_MODULES}      robot_utils    zbsync  zbsync_xport_ui
@{UNINSTALL_MODULES}    ${NONE}
${REPETITION}       5



*** Test Cases ***
Test Lot of records working pipeline call other pipeline without duplicates Run Once
    Test Lot of records working pipeline call other pipeline without duplicates

Test Lot of records working pipeline call other pipeline without duplicates Run Repeated
    FOR  ${i}  IN RANGE  ${REPETITION}
        Log  This is repetition ${i}
        Wait Until Keyword Succeeds    10 min  10 s  Test Lot of records working pipeline call other pipeline without duplicates
    END
*** Keywords ***
Test Lot of records working pipeline call other pipeline without duplicates
    ## make csv file
    Odoo Search Unlink    zbs.pipeline    []
    Odoo Search Unlink    zbs.instance    []
    ${count}=  Odoo Search Unlink  res.partner  [('name', '=ilike', 'xxx%')]

    ${count}=  Odoo Search  res.partner  [('name', '=', 'xxxAaron Wallace')]  count=True
    Assert  ${count} == 0  There should not be an xxxAaron Wallace at start of the test

    Goto Zync
    ${pipe2}=    Import Pipeline    pipe2    ${SUITE_PATH}/pipe2.json
    ${pipe1}=    Import Pipeline    pipe1_${TOKEN}    ${SUITE_PATH}/pipe1.json

    Odoo Load Data    ${SUITE_PATH}/${DATA_FILE}
    Go To    ${ODOO_URL}/web#id=${pipe1}&model=zbs.pipeline&view_type=form
    Capture Page Screenshot

    Wait To Click    css=button[name='start_from_ui_like_cronjob']
    Wait Queuejobs Done
    Zync Run Cron Pipeline Pusher

    Wait Queuejobs Done

    # TODO Check for serialize access errors in postgres log ....

    Log    Check that there are no duplicates for initial data in instances
    ${partners}=    Odoo Search Records    res.partner    [('street2', '!=', False)]
    ${index}=    Set Variable    0
    ${len}=    Evaluate    len($partners)

    ${initial_datas}=    Odoo Search Read Records    zbs.instance    []    initial_data
    FOR    ${partner}    IN    @{partners}
        Log To Console    Checking duplicate for ${partner['name']} in ${partner.street2}
        ${count}=    Set Variable    0
        FOR    ${instance}    IN    @{initial_datas}
            ${strinstance}=  Evaluate  str(${instance}).replace('"', "")
            IF    '${partner.street2}' in "${strinstance}"
                ${count}=    Evaluate    ${count} + 1
            END
        END
        # ${count}=    Odoo Search    zbs.instance    [('initial_data', 'like', '%${partner.street2}%')]    count=1
        Log2    Count is: ${count} at ${{ ${index} + 1}} of ${len}
        Assert    ${count} == 1
        ${index}=    Evaluate    ${index} + 1
    END



Make Demo Data    [Arguments]    ${amount}
    ${records}=    fake data    ${amount}
    FOR    ${record}    IN    @{records}
        Log    ${record}
        Odoo Create    res.partner    ${record}
    END
