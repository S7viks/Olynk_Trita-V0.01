from fastapi import FastAPI

import os

from trita_api.routes.auth import router as auth_router
from trita_api.routes.csv import router as csv_router
from trita_api.routes.identity import router as identity_router
from trita_api.routes.metrics import router as metrics_router
from trita_api.routes.decisions import router as decisions_router
from trita_api.routes.causal import router as causal_router
from trita_api.routes.proactive import router as proactive_router
from trita_api.routes.chat import router as chat_router
from trita_api.routes.reports import router as reports_router
from trita_api.routes.dev_auth import router as dev_auth_router
from trita_api.routes.dev_shopify import router as dev_shopify_router
from trita_api.routes.integrations import router as integrations_router
from trita_api.routes.llm import router as llm_router
from trita_api.routes.sources import router as sources_router
from trita_api.routes.shopify import router as shopify_router
from trita_api.routes.tenant import router as tenant_router
from trita_api.routes.settings import router as settings_router
from trita_api.routes.onboarding import router as onboarding_router

app = FastAPI(
    title="Trita API",
    version="0.0.1",
    description="Third Observer API — tenant-scoped inventory intelligence",
)

app.include_router(auth_router)
app.include_router(tenant_router)
app.include_router(settings_router)
app.include_router(onboarding_router)
app.include_router(integrations_router)
app.include_router(csv_router)
app.include_router(identity_router)
app.include_router(metrics_router)
app.include_router(reports_router)
app.include_router(decisions_router)
app.include_router(causal_router)
app.include_router(proactive_router)
app.include_router(chat_router)
app.include_router(llm_router)
# Shopify before generic /v1/sources/{source}/* so POST .../shopify/sync is not shadowed
app.include_router(shopify_router)
app.include_router(sources_router)
if os.environ.get("ENVIRONMENT", "development") == "development":
    app.include_router(dev_auth_router)
    app.include_router(dev_shopify_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness for Render VA-10 and local probes."""
    return {"status": "ok", "service": "trita-api"}
