# Part of Zebroo GmbH. See LICENSE file for full copyright and licensing details (www.zebroo.de/license).
from odoo import fields, models
import logging

from sqlalchemy import create_engine

logger = logging.getLogger("ZYNC SQL CONNECTION")


def legacy_row_to_dict(row):
    """
    Convert a LegacyRow object to a dictionary.
    """
    return {column: local_getattr(row, column) for column in row.keys()}


def local_getattr(row, column):
    value = getattr(row, column)
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return value


def legacy_rows_to_json(rows):
    """
    Convert a list of LegacyRow objects to a JSON string.
    """
    result = [legacy_row_to_dict(row) for row in rows]
    return result


class SnowflakeConnection(models.Model):
    _name = "zbs.connection.snowflake"
    _description = "Snowflake Connection"

    name = fields.Char("Name", required=True)
    account = fields.Char("Account", required=True)
    username = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)
    database = fields.Char("Database", required=True)
    schema = fields.Char("Schema", required=True)
    warehouse = fields.Char("Warehouse", required=True)

    def fetchall(self, sql):
        engine = create_engine(
            (
                f"snowflake://{self.username}:{self.password}@"
                f"{self.account}/{self.database}/{self.schema}?"
                f"warehouse={self.warehouse}"
            )
        )
        connection = engine.connect()
        results = connection.execute(sql).fetchall()
        results = legacy_rows_to_json(results)
        return results
