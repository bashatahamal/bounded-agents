import structlog

from graphs.main import graph
from integrations.sheet import GoogleSheetsClient

logger = structlog.get_logger(__name__)


class CompanyResearch:
    def __init__(self, spreadsheet_id: str):
        logger.info(
            "Initializing CompanyResearch",
            spreadsheet_id=spreadsheet_id,
        )

        self.graph = graph
        self.sheet = GoogleSheetsClient(spreadsheet_id=spreadsheet_id)

    def run(
        self,
        worksheet_input: str,
        input_column_name: str = "Company Name",
        worksheet_output: str = "Review Company",
    ):
        logger.info(
            "Starting company research",
            worksheet_input=worksheet_input,
            input_column_name=input_column_name,
            worksheet_output=worksheet_output,
        )

        sheet_data = self.sheet.read_cell(worksheet_name=worksheet_input)

        companies = [
            row[input_column_name]
            for row in sheet_data
            if row.get(input_column_name)
        ]

        logger.info("Companies loaded", count=len(companies))

        for idx, company_name in enumerate(companies, start=1):
            logger.info(
                "Processing company",
                company=company_name,
                progress=f"{idx}/{len(companies)}",
            )

            try:
                result = self.graph.invoke({"company_name": company_name})
                summary = result.get("summary", "")

                self.sheet.append_rows(
                    columns=["Company", "Summary"],
                    values=[[company_name, summary]],
                    worksheet_name=worksheet_output,
                )

                logger.info(
                    "Company completed",
                    company=company_name,
                    summary_length=len(summary),
                )

            except Exception as e:
                logger.error(
                    "Company failed",
                    company=company_name,
                    error=str(e),
                    exc_info=True,
                )


if __name__ == "__main__":
    research = CompanyResearch(
        spreadsheet_id="1aA6b3Jzx4wH-EgGb29RLMOs-G1gOvlpXgwQSBMoitLM"
    )
    research.run(
        input_column_name="Company Name",
        worksheet_input="Sheet1",
        worksheet_output="Summary",
    )
