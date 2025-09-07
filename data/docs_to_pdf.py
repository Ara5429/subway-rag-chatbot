from datasets import load_dataset
from fpdf import FPDF

from huggingface_hub import notebook_login
notebook_login('hf_your_token_here')

ds = load_dataset("aracho1029384/subway-docs")
# 예시. 실제 컬럼명 확인 후 아래 코드에서 'station'과 'text'를 맞게 설정하세요.

pdf = FPDF()
pdf.add_font("NanumGothic", "", "NanumGothic.ttf", uni=True)
pdf.set_font("NanumGothic", size=12)

station_docs = {}
for row in ds['train']:
    station = row['metadata']['station']
    content = row['text']
    if station not in station_docs:
        station_docs[station] = []
    station_docs[station].append(content)

for station, texts in station_docs.items():
    pdf.add_page()
    pdf.set_font("NanumGothic", size=14)
    pdf.cell(0, 10, station, ln=True)
    pdf.set_font("NanumGothic", size=12)
    body = '\n\n'.join(texts)
    pdf.multi_cell(0, 10, body)

pdf.output("subway_station_docs.pdf")