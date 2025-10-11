from cdp_use import CDPClient
from pydantic import BaseModel


class BrowserSession(BaseModel):
    cdp_client: CDPClient

    model_config = {"arbitrary_types_allowed": True}

    def dispose(self):
        pass
