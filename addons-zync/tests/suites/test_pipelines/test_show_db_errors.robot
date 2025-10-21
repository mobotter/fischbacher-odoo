*** Settings ***
Documentation       Test Triggers

Library             OperatingSystem
Resource            ../../keywords/zync.robot

Test Setup          Setup Test
Test Teardown       Teardown Test


*** Variables ***
@{INSTALL_MODULES}      robot_utils    zbsync
@{UNINSTALL_MODULES}    ${NONE}


*** Test Cases ***
Test Run into db exception
    ## make csv file
    Goto Zync
    Screenshot

	Odoo Sql  delete from res_partner_title where name::varchar = 'DOPPELT';
	Run Keyword And Ignore Error  Odoo Sql  ALTER TABLE res_partner_title DROP CONSTRAINT unique_name;
	Odoo Sql  ALTER TABLE res_partner_title ADD CONSTRAINT unique_name UNIQUE (name);

    ${pipeline_id}=    Import Pipeline    doppelt.import_${TOKEN}    ${SUITE_PATH}/data/duplicate_item_create_and_hit_error.json

    GoTo View  zbs.pipeline  ${pipeline_id}
    Wait To Click    button[name = 'start_from_ui_like_cronjob']
    ${instance_id}=    Get Instance ID From Url    zbs.instance
    Run Keyword And Ignore Error  Zync Complete Run    ${instance_id}
    Wait Queuejobs Done

	Odoo Sql  alter table res_partner_title DROP CONSTRAINT unique_name;

    Goto View  zbs.instance  ${instance_id}

    Wait To Click  div.zbs-batch.failed
    Wait To Click  tr.o_data_row.text-danger td  position=3
    JS Exists Element  textarea  duplicate key value violates unique constraint
