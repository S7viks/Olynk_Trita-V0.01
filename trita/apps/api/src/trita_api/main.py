from fastapi import FastAPI

import os

from trita_api.routes.dev_shopify import router as dev_shopify_router
from trita_api.routes.llm import router as llm_router
from trita_api.routes.shopify import router as shopify_router
from trita_api.routes.tenant import router as tenant_router

app = FastAPI(
    title="Trita API",
    version="0.0.1",
    description="Third Observer API — tenant-scoped inventory intelligence",
)

app.include_router(tenant_router)
app.include_router(llm_router)
app.include_router(shopify_router)
if os.environ.get("ENVIRONMENT", "development") == "development":
    app.include_router(dev_shopify_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness for Render VA-10 and local probes."""
    return {"status": "ok", "service": "trita-api"}
