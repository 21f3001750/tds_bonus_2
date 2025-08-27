Quick start:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload


Project Description

This application takes bulk text input (such as plain prose or markdown) and automatically generates a PowerPoint presentation that follows a chosen visual template. The system first parses the input text by breaking it down into hierarchical sections. Headings and subheadings are detected to define slide titles, while paragraphs and lists are mapped to the slide body as bullet points or narrative text. This ensures that each logical chunk of content is placed on a separate slide, maintaining readability and flow.

Once the content is structured, the app applies the chosen PowerPoint template to preserve visual consistency. The template provides predefined slide layouts, fonts, colors, and background designs. By mapping parsed content into these layouts, the tool ensures that slides are visually appealing without requiring manual formatting. Images or media assets included in the template are reused, and placeholders are automatically filled with the corresponding text content.

The final result is a professional-looking .pptx file where the user’s raw text has been transformed into a presentation that is both visually coherent and stylistically aligned with the template. This approach significantly reduces the manual effort of creating slides and enables quick turnaround for academic, business, or personal use.