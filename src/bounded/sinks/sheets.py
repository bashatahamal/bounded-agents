from __future__ import annotations

import gspread
import structlog

from bounded.credentials import load_json_credentials
from bounded.sinks.base import Cell

logger = structlog.get_logger(__name__)


class GoogleSheetsSink:
    """Reads/writes rows against a single Google Spreadsheet via a service account.

    `credentials` accepts a dict, a file path, a base64 string, or a raw
    JSON string (see `bounded.credentials.load_json_credentials`).
    """

    def __init__(self, spreadsheet_id: str, credentials: str | dict):
        creds_dict = (
            credentials if isinstance(credentials, dict) else load_json_credentials(credentials)
        )
        logger.info("Connecting to Google Sheets", spreadsheet_id=spreadsheet_id)
        self._client = gspread.service_account_from_dict(creds_dict)
        self._spreadsheet = self._client.open_by_key(spreadsheet_id)
        self.spreadsheet_id = spreadsheet_id

    def worksheet_names(self) -> list[str]:
        return [ws.title for ws in self._spreadsheet.worksheets()]

    def read_rows(self, worksheet_name: str, range_name: str | None = None) -> list[dict[str, str]]:
        sheet = self._spreadsheet.worksheet(worksheet_name)
        raw = sheet.get(range_name) if range_name else sheet.get_all_values()
        if not raw:
            return []
        headers, *rows = raw
        return [{headers[i]: value for i, value in enumerate(row)} for row in rows]

    def write(self, columns: list[str], rows: list[list[Cell]], *, destination: str) -> None:
        worksheet_name = destination
        if worksheet_name in self.worksheet_names():
            worksheet = self._spreadsheet.worksheet(worksheet_name)
            if worksheet.get_all_values() == [[]]:
                worksheet.insert_row(columns, 1, inherit_from_before=False)
        else:
            worksheet = self._spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=max(10, len(columns))
            )
            worksheet.insert_row(columns, 1, inherit_from_before=False)

        headers = worksheet.row_values(1)
        if len(columns) != len(headers):
            raise ValueError(
                f"Column count mismatch: {len(columns)} column(s) given, "
                f"worksheet '{worksheet_name}' has header(s) {headers}."
            )

        worksheet.append_rows(rows)
