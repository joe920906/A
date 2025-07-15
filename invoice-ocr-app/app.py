import streamlit as st
from PIL import Image
import pytesseract
import openai
import openpyxl
import io

# 設定 Tesseract 路徑（如部署到 Linux 伺服器記得安裝 tesseract）
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# 設定 OpenAI API key
openai.api_key = "sk-proj-O0xMB9DgtWwkHP47Bi0PT3BlbkFJqO19E8vnaZ9xxKwCpmZ"  # ⚠️ 建議放到 .env 或 Streamlit Secret

st.title("📄 統一發票辨識系統")
st.write("上傳一張發票圖片，系統會進行 OCR 與 AI 資訊整理，並產出 Excel 檔案。")

uploaded_file = st.file_uploader("請選擇發票圖片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='上傳的發票', use_column_width=True)

    # OCR 辨識
    with st.spinner("🔍 OCR 辨識中..."):
        ocr_text = pytesseract.image_to_string(image, lang='chi_tra+eng')

    st.subheader("📄 OCR 原始文字")
    st.text(ocr_text)

    # 呼叫 OpenAI 來整理內容
    prompt = f"""
    以下是一張發票的文字內容，請幫我萃取以下欄位：
    1. 發票號碼（兩碼英文+8碼數字）
    2. 發票日期（民國年格式或西元格式）
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

    with st.spinner("🤖 呼叫 OpenAI 萃取資訊中..."):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        extracted_text = response.choices[0].message["content"]

    st.subheader("🤖 OpenAI 整理結果")
    st.text(extracted_text)

    # 匯出 Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "發票辨識"
    ws.append(["欄位", "內容"])
    for line in extracted_text.strip().split('\n'):
        if "：" in line:
            key, value = line.split("：", 1)
            ws.append([key.strip(), value.strip()])

    # 轉成 bytes，提供下載
    output = io.BytesIO()
    wb.save(output)
    st.download_button(
        label="📥 下載 Excel 結果",
        data=output.getvalue(),
        file_name="發票辨識結果.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
