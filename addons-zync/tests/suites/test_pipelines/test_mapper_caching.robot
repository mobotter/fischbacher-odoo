*** Comments ***
# odoo-require: zbsync, robot_utils


*** Settings ***
Documentation       Creates demo data and a mapper to check if cache keywords work.

Library             OperatingSystem
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
# ${DATA_FILE}    data.big/res.partner.csv
${DATA_FILE}    data/mapper_caching.json
${SNIPPET_MODE}         0
@{INSTALL_MODULES}      robot_utils    zbsync  zbsync_xport_ui
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Test Simple Mapper if caching works
    ## make csv file

    Goto Zync
    ${pipe}=    Import Pipeline    pipe_${TOKEN}    ${SUITE_PATH}/data/test_mapper_caching.json

    Go To    ${ODOO_URL}/web#id=${pipe}&model=zbs.pipeline&view_type=form

    Wait To Click    css=button[name='start_from_ui_like_cronjob']
	${instanceid}=  Get Instance ID From Url  zbs.instance

    Wait Queuejobs Done
    Zync Run Cron Pipeline Pusher

    Wait Queuejobs Done

	${dbpipe}=  Odoo Read Field  zbs.instance  ${instanceid}  state

	Should Be Equal As Strings  ${dbpipe}  success


*** Keywords ***
