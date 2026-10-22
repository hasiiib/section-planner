from pathlib import Path
from uiu.parser import parse_pdf
from uiu.scheduler import is_conditional

def test_clipped_pdf_conditional_markers():
    src=Path(__file__).resolve().parents[1]/'Fall_2026_offerings.pdf'
    if not src.exists():return
    records,_,_=parse_pdf(src)
    found={x.serial for x in records if is_conditional(x)}
    assert {16,56,143,145,148,152,750}.issubset(found)
    assert next(x for x in records if x.serial==750).section=='BB'
