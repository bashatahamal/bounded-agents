import gspread
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str | None = None):
        logger.info("Initialize Google Sheets Client")
        self.client = None
        self.workspace = None
        self._connect()
        if spreadsheet_id:
            self.set_workspace(spreadsheet_id=spreadsheet_id)

    def _connect(self):
        try:
            logger.info("Connecting to google-spreadsheet...")
            self.client = gspread.service_account_from_dict(
                settings.GOOGLE_SHEET_ACCESS_DICT
            )
            logger.info("Connected google-spreadsheet!")
        except Exception as e:
            raise Exception(f"Failed to connect to Google Sheets: {str(e)}")

    def set_workspace(self, spreadsheet_id: str):
        try:
            self.workspace = self.client.open_by_key(spreadsheet_id)
            self.spreadsheet_id = spreadsheet_id
        except Exception as e:
            raise Exception(f"Failed to connect to Google Sheets: {str(e)}")

    def get_worksheet_names(self) -> list[str]:
        try:
            worksheets = self.workspace.worksheets()
            return [ws.title for ws in worksheets]
        except Exception as e:
            raise Exception(f"Failed to get worksheet names: {str(e)}")

    def read_cell(
        self,
        range_name: str | None = None,
        worksheet_name: str = None,
    ) -> list[list[str]]:
        try:
            sheet = self.workspace.worksheet(worksheet_name)
            if range_name is not None:
                val_worksheet = sheet.get(range_name)
            else:
                val_worksheet = sheet.get_all_values()

            # Convert to list of lists format
            if not val_worksheet:
                return []

            # Get title
            headers = val_worksheet[0]

            # Pair column with values
            values = [
                {headers[i]: value for i, value in enumerate(row)}
                for row in val_worksheet[1:]
            ]
            return values

        except Exception as e:
            raise Exception(f"Failed to read range {range_name}: {str(e)}")

    def append_rows(
        self,
        columns: list[str],
        values: list[list[str | int | float]],
        worksheet_name: str = None,
    ) -> bool:
        try:
            if worksheet_name in self.get_worksheet_names():
                worksheet = self.workspace.worksheet(worksheet_name)
                # check if worksheet is empty
                all_val = worksheet.get_all_values()
                if all_val == [[]]:
                    worksheet.insert_row(columns, 1, inherit_from_before=False)
            else:
                # create worksheet
                self.workspace.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=10,
                )
                worksheet = self.workspace.worksheet(worksheet_name)
                worksheet.insert_row(columns, 1, inherit_from_before=False)

            # get column headers
            headers = worksheet.row_values(1)

            if len(columns) != len(headers):
                raise ValueError(
                    f"Column count mismatch: {len(columns)=} != {len(headers)=}. \n"
                    f"{headers=}\n"
                    f"Please ensure the number of columns matches the header count."
                )

            worksheet.append_rows(values)
            return True

        except Exception as e:
            raise Exception(f"Failed to append rows: {str(e)}")


if __name__ == "__main__":
    # Example usage
    gs_cli = GoogleSheetsClient(
        spreadsheet_id="1Jz_FgPhoU5cfWR_vgNIAFrhJu5quipcWVtiM4G6y5fM"
    )
    worksheet_names = gs_cli.get_worksheet_names()
    print("Worksheets:", worksheet_names)

    values = gs_cli.read_cell(worksheet_name=worksheet_names[0])
    print("Values in first worksheet:", values)

    # columns = [
    #     "Company",
    #     "Overview",
    #     "Bidang",
    #     "Product",
    #     "Official Website",
    # ]
    # values = [
    #     [
    #         f"Company {idx}",
    #         f"Overview {idx}",
    #         f"Bidang {idx}",
    #         f"Product {idx}",
    #         f"Official Website {idx}",
    #     ]
    #     for idx in range(10)
    # ]
    # gs_cli.append_rows(
    #     columns=columns,
    #     values=values,
    #     worksheet_name="comp-summary",
    # )
