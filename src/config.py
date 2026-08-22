from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
EXCEL_FILE = DATA_DIR / "ParcelPilot_Assessment_Data.xlsx"

STORAGE_DIR = BASE_DIR / "storage"


# Dataset reference time
DATASET_SNAPSHOT = "2026-08-16 11:00"
TIMEZONE = "Asia/Kolkata"
CURRENCY = "INR"


# Source authority
SOURCE_PRIORITY = {
    "customer_agreement": 1,
    "current_policy": 2,
    "current_sop": 2,
    "product_operations": 3,
    "historical_ticket": 4,
    "deprecated_policy": 5
}


# Document metadata
DOCUMENT_METADATA = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "source_type": "current_policy",
        "status": "current",
        "priority": 2
    },
    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "source_type": "deprecated_policy",
        "status": "deprecated",
        "priority": 5
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "source_type": "current_sop",
        "status": "current",
        "priority": 2
    },
    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "source_type": "product_operations",
        "status": "current",
        "priority": 3
    },
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "source_type": "customer_agreement",
        "status": "current",
        "priority": 1,
        "account_id": "ACCT-001"
    },
    "06_LumenWorks_Service_Agreement.pdf": {
        "source_type": "customer_agreement",
        "status": "current",
        "priority": 1,
        "account_id": "ACCT-002"
    }
}


# Account-specific agreements
ACCOUNT_AGREEMENTS = {
    "ACCT-001": "05_Northstar_Logistics_Enterprise_Agreement.pdf",
    "ACCT-002": "06_LumenWorks_Service_Agreement.pdf"
}