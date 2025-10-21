*** Settings ***
Library         OperatingSystem
Library         RequestsLibrary
Documentation   Tests if per header a database can be chosen.
Resource        ../../keywords/zync.robot
Test Setup      Setup Test
Test Teardown       Teardown Test


*** Variables ***
${SNIPPET_MODE}    ${FALSE}
@{INSTALL_MODULES}  robot_utils  zbsync
@{UNINSTALL_MODULES}  ${NONE}

*** Keywords ***

Copy Odoo 2 DB2
    Odoo Command  kill odoo odoo_queuejobs odoo_cronjobs
    Odoo Command  restart postgres
    Odoo Command  up -d postgres
    Odoo Command  docker wait-for-container-postgres
    Odoo Command  psql --sql "DROP DATABASE IF EXISTS db2;"
    Odoo Command  docker wait-for-container-postgres
    Odoo Command  psql --sql "CREATE DATABASE db2 WITH TEMPLATE ${ROBO_ODOO_DB};"
    Run Keyword And Ignore Error  Odoo Command  psql --sql "CREATE EXTENSION dblink;"
    Odoo Command  psql --sql "SELECT dblink_exec('dbname=db2', 'INSERT INTO res_partner(name) values(''diego maradona'');') "
    Odoo Command  up -d
    Odoo Command  up -d odoo
    Odoo Command  docker wait-for-container-postgres

*** Test Cases ***


Test Receiver With Two Databases


	Goto Zync
	${sync_pipeline_id}=  Import Pipeline  receiver_db2_${TOKEN}  ${SUITE_PATH}/pipeline.json
    Copy Odoo 2 DB2
    Log To Console      Now pipeline with web endpoint is in db2 odoo.
    Log To Console      Deactivate web

	Log To Console      Url of odoo is ${ODOO_URL}
    ${headers}=         Create Dictionary     dbname=db2
    ${response}=        GET    ${ODOO_URL}/zync/test_2companies  headers=${headers}  expected_status=200
    Log                 ${response.json()}
    Assert              "diego maradona" in str(${response.json()})

    ${response}=        GET    ${ODOO_URL}/zync/test_2companies  expected_status=200
    Log                 ${response.json()}
    Assert              "diego maradona" not in str(${response.json()})
