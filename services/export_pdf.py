import io
from xhtml2pdf import pisa

def generate_pdf_bytes(html_content: str) -> bytes:
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.StringIO(html_content),
        dest=result
    )
    if pisa_status.err:
        raise Exception("Failed to generate PDF")
    return result.getvalue()

def build_dashboard_html(kpis: dict, tables: list[dict]) -> str:
    rows = ""
    for t in tables:
        rows += f"<h3>{t['title']}</h3><p>{t['body']}</p>"
    return f"""
    <html><head><meta charset="utf-8">
    <style>
      body {{ font-family: Arial, sans-serif; padding: 20px; }}
      h1 {{ color: #1a1a2e; }}
      .kpi {{ display: inline-block; margin: 10px; padding: 15px;
               background: #f0f4ff; border-radius: 8px; min-width: 150px; }}
      .kpi-value {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
    </style></head>
    <body>
    <h1>Báo cáo Dealer Report</h1>
    <div>
      {''.join(f'<div class="kpi"><div>{k}</div><div class="kpi-value">{v}</div></div>' for k, v in kpis.items())}
    </div>
    {rows}
    </body></html>
    """
