"""Where the system under test lives. Override any value with an env var."""

import os

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
USERSERVICE_URL = os.getenv("USERSERVICE_URL", "http://localhost:8081")
CONTACTS_URL = os.getenv("CONTACTS_URL", "http://localhost:8082")
LEDGERWRITER_URL = os.getenv("LEDGERWRITER_URL", "http://localhost:8083")
BALANCEREADER_URL = os.getenv("BALANCEREADER_URL", "http://localhost:8084")
HISTORY_URL = os.getenv("HISTORY_URL", "http://localhost:8085")
WIREMOCK_URL = os.getenv("WIREMOCK_URL", "http://localhost:8086")

# kubernetes-manifests/config.yaml
LOCAL_ROUTING_NUM = os.getenv("LOCAL_ROUTING_NUM", "883745000")
DEMO_USERNAME = os.getenv("DEMO_USERNAME", "testuser")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "bankofanthos")

# routing number of "some other bank" used for external deposits
EXTERNAL_ROUTING_NUM = "111111111"
EXTERNAL_ACCOUNT_NUM = "9099791699"

# path to the Bank of Anthos checkout (component tests import the frontend from it)
BOA_REPO = os.getenv(
    "BOA_REPO",
    os.path.join(os.path.dirname(__file__), "..", "..", "bank-of-anthos"),
)
