import io
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def generate_ppt_bytes(kpis: dict[str, str], title: str = "Báo cáo Dealer Report") -> bytes:
    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    slide.placeholders[1].text = "Báo cáo Vận động Bán sỉ"

    kpi_slide = prs.slides.add_slide(prs.slide_layouts[6])
    kpi_slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.6)).text_frame.add_paragraph().text = "Chỉ số Hiệu suất Chính (Key Performance Indicators)"

    cols = 4
    for i, (label, value) in enumerate(kpis.items()):
        col_i = i % cols
        row_i = i // cols
        left   = Inches(0.3 + col_i * 3.2)
        top    = Inches(1.2 + row_i * 2.0)
        box    = kpi_slide.shapes.add_textbox(left, top, Inches(3.0), Inches(1.6))
        tf     = box.text_frame
        tf.word_wrap = True
        p_label       = tf.add_paragraph()
        p_label.text  = label
        p_label.runs[0].font.size = Pt(12)
        p_value       = tf.add_paragraph()
        p_value.text  = value
        run           = p_value.runs[0]
        run.font.size = Pt(24)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
