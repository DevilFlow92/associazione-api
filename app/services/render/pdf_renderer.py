from __future__ import annotations

from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.exceptions.template import TemplateRenderError

# --no-sandbox è necessario perché il container Docker gira come root e il
# sandbox Chromium richiede privilegi (user namespaces) tipicamente assenti
# nei runner CI e nei container di produzione senza flag aggiuntivi.
_LAUNCH_ARGS = ["--no-sandbox"]

_PAGEDJS_PATH = Path(__file__).parent / "assets" / "paged.polyfill.js"
_PAGEDJS_SOURCE = _PAGEDJS_PATH.read_text(encoding="utf-8")

# window.PagedConfig è l'hook ufficiale del polyfill (vedi README nel
# pacchetto pagedjs): "after" viene invocato con l'oggetto flow non appena
# la Previewer ha finito di impaginare, quindi è il segnale deterministico
# di completamento — non serve indovinare un selettore o un timeout.
_PAGEDJS_CONFIG_SCRIPT = """
window.PagedConfig = {
    after: () => { window.__pagedjsDone = true; },
};
"""

_PAGINATION_TIMEOUT_MS = 10_000


async def build_pdf(html: str) -> bytes:
    """Renderizza l'HTML impaginato da paged.js e ne cattura il PDF."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(args=_LAUNCH_ARGS)
        try:
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await page.set_content(html)
                # Il config va impostato prima che il polyfill venga eseguito:
                # legge window.PagedConfig in modo sincrono all'avvio.
                await page.add_script_tag(content=_PAGEDJS_CONFIG_SCRIPT)
                await page.add_script_tag(content=_PAGEDJS_SOURCE)
                try:
                    await page.wait_for_function(
                        "window.__pagedjsDone === true",
                        timeout=_PAGINATION_TIMEOUT_MS,
                    )
                except PlaywrightTimeoutError as e:
                    raise TemplateRenderError(
                        "Impaginazione PDF non completata in tempo"
                    ) from e
                return await page.pdf(format="A4")
            finally:
                await context.close()
        finally:
            await browser.close()
