from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import io, json

from .llm import call_llm, build_outline_prompt
from .pptx_utils import build_presentation

app = FastAPI(title="Your Text, Your Style – PPTX Generator")

# serve static files and templates (assumes app/static and app/templates exist)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(
    request: Request,
    input_text: str = Form(...),
    guidance: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    base_url: Optional[str] = Form(None),
    speaker_notes: Optional[str] = Form(None),
    template: Optional[UploadFile] = File(None),   # template is optional now
):
    # If neither template nor input_text provided -> error (input_text is required by Form(...), but double-check)
    if not input_text or not input_text.strip():
        raise HTTPException(400, "Please paste your content in the text box or upload a text/markdown file.")

    template_bytes = None

    if template:  # only process if a file was uploaded
        try:
            # Some ASGI servers' UploadFile may not support seek, so guard
            size = await template.seek(0, io.SEEK_END)
            await template.seek(0)
        except Exception:
            size = None

        if size and size > 20 * 1024 * 1024:
            raise HTTPException(413, "Template too large (max 20MB).")

        template_bytes = await template.read()

    # --- Build outline via LLM or fallback heuristic ---
    outline = None
    if provider and api_key:
        try:
            prompt = build_outline_prompt(input_text, guidance or "", bool(speaker_notes))
            content = call_llm(provider, api_key, model or "", prompt, base_url)
            # Try to parse strict JSON from LLM
            outline = json.loads(content)
            if "slides" not in outline:
                raise ValueError("LLM did not return slides list.")
        except Exception:
            # If parsing/call fails, fall back to heuristic
            outline = heuristic_outline(input_text, guidance or "", bool(speaker_notes))
    else:
        outline = heuristic_outline(input_text, guidance or "", bool(speaker_notes))

    # --- Build PowerPoint (template_bytes may be None) ---
    pptx_bytes = build_presentation(template_bytes, outline)
    filename = "generated_presentation.pptx"
    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

def heuristic_outline(text: str, guidance: str, speaker_notes: bool):
    """
    Very small heuristic to split pasted text or markdown into slides.
    - Splits on markdown headings (#) and blank lines.
    - Creates slides with short bullets.
    """
    blocks = []
    cur = []
    lines = text.splitlines()
    for ln in lines:
        if ln.strip().startswith("#"):
            if cur:
                blocks.append(" ".join(cur).strip())
                cur = []
            blocks.append(ln.strip())
        elif ln.strip():
            cur.append(ln.strip())
        else:
            if cur:
                blocks.append(" ".join(cur).strip())
                cur = []
    if cur:
        blocks.append(" ".join(cur).strip())

    slides = []
    for b in blocks:
        title = b.lstrip("# ").split(". ")[0][:80]
        parts = [p.strip("-• ").strip() for p in b.split(". ") if p.strip()]
        bullets = [p[:100] for p in parts[:5]]
        if not bullets:
            # fallback: split lines into bullets
            lines_b = [ln.strip() for ln in b.splitlines() if ln.strip()]
            bullets = lines_b[:5] if lines_b else [b[:100]]
        slide = {"title": title or "Section", "bullets": bullets}
        if speaker_notes:
            slide["notes"] = f"Discuss: {title}"
        slides.append(slide)

    # cap slide count
    if len(slides) > 20:
        slides = slides[:20]

    return {"slides": slides}