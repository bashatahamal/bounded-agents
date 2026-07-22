from __future__ import annotations

import structlog

from bounded.sinks import GoogleSheetsSink
from company_research.graph import graph
from company_research.settings import get_settings

logger = structlog.get_logger(__name__)


class CompanyResearch:
    def __init__(self, spreadsheet_id: str):
        logger.info("Initializing CompanyResearch", spreadsheet_id=spreadsheet_id)
        settings = get_settings()
        self.graph = graph
        self.sink = GoogleSheetsSink(
            spreadsheet_id=spreadsheet_id,
            credentials=settings.GOOGLE_SHEET_ACCESS_CREDS,
        )

    def run(
        self,
        worksheet_input: str,
        input_column_name: str = "Company Name",
        worksheet_output: str = "Review Company",
    ) -> None:
        logger.info(
            "Starting company research",
            worksheet_input=worksheet_input,
            input_column_name=input_column_name,
            worksheet_output=worksheet_output,
        )

        rows = self.sink.read_rows(worksheet_name=worksheet_input)
        companies = [row[input_column_name] for row in rows if row.get(input_column_name)]

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

                self.sink.write(
                    columns=["Company", "Summary"],
                    rows=[[company_name, summary]],
                    destination=worksheet_output,
                )

                logger.info("Company completed", company=company_name, summary_length=len(summary))
            except Exception as e:
                logger.error("Company failed", company=company_name, error=str(e), exc_info=True)
