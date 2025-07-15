import streamlit as st
from google.cloud import vision
import io
import openai
import openpyxl

# 載入 Google Vision API key json 路徑
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your/google-credentials.json'

# 初始化 Google Vision 客戶端
client = vision.ImageAnnotatorClient()

# OpenAI API Key
openai.api_key = 'sk-proj-O0xMB9DgtWwkHP47Bi0PT3BlbkFJqO19E8vnaZ9xxKwCpmZy'

st.title("📄 發票辨識系統（Google Vision OCR + ChatGPT）")
uploaded_file = st.file_uploader("請上傳發票圖片", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image_bytes = uploaded_file.read()

    # 呼叫 Google Vision OCR
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if texts:
        ocr_text = texts[0].description
        st.subheader("OCR 辨識文字結果")
        st.text(ocr_text)

        # 用 ChatGPT 幫忙萃取欄位
        prompt = f"""
以下是一張發票的文字內容，請幫我萃取以下欄位：
1. 發票號碼（兩碼英文+8碼數字）
2. 發票日期（民國年或西元年格式）
3. 總計（總金額）
4. 商家名稱

格式如下：
發票號碼：...
商家：...
日期：...
金額：...

發票內容如下：
{ocr_text}
"""

        with st.spinner("🤖 呼叫 ChatGPT 萃取資訊中..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            extracted_text = response.choices[0].message.content

        st.subheader("ChatGPT 萃取結果")
        st.text(extracted_text)

        # 輸出 Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "發票辨識"
        ws.append(["欄位", "內容"])
        for line in extracted_text.strip().split('\n'):
            if "：" in line:
                key, value = line.split("：", 1)
                ws.append([key.strip(), value.strip()])

        output = io.BytesIO()
        wb.save(output)

        st.download_button(
            label="📥 下載 Excel 結果",
            data=output.getvalue(),
            file_name="發票辨識結果.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    else:
        st.error("無法辨識任何文字，請換張清晰的圖片。")
