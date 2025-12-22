import argparse
import sys

import structlog
from dotenv import load_dotenv

from services.company_research import CompanyResearch

load_dotenv()

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI-powered company research tool",
    )

    parser.add_argument(
        "spreadsheet_id",
        help="Google Sheets spreadsheet ID",
    )

    parser.add_argument(
        "--input-worksheet",
        default="Names",
        help="Worksheet containing company names",
    )

    parser.add_argument(
        "--input-column",
        default="Company Name",
        help="Column containing company names",
    )

    parser.add_argument(
        "--output-worksheet",
        default="Review Company",
        help="Worksheet to write summaries",
    )

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        runner = CompanyResearch(spreadsheet_id=args.spreadsheet_id)
        runner.run(
            worksheet_input=args.input_worksheet,
            input_column_name=args.input_column,
            worksheet_output=args.output_worksheet,
        )

        logger.info("Research completed successfully")

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
