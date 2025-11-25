import streamlit as st
import requests
import json
import base64
import time

# --- 1. 設定頁面 (手機版面優化) ---
st.set_page_config(
    page_title="腎友食安守門員",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. CSS 美化 (修復輸入框位置、大字體、大按鈕) ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    
    /* === 全域字體放大 === */
    h1 { font-size: 3rem !important; font-weight: 900 !important; color: #1e3a8a !important; }
    h2 { font-size: 2.2rem !important; font-weight: 800 !important; color: #1e40af !important; }
    h3 { font-size: 1.8rem !important; font-weight: 700 !important; }
    p, .stMarkdown, li { font-size: 1.2rem !important; line-height: 1.6 !important; }
    
    /* === 按鈕樣式 === */
    .stButton>button { 
        border-radius: 12px; 
        height: 4em; 
        font-weight: bold; 
        width: 100%; 
        font-size: 1.3em !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* === 狀態卡片 === */
    .status-card {
        background-color: #e0f2fe; 
        border-left: 8px solid #0284c7;
        padding: 20px; 
        border-radius: 10px; 
        color: #0c4a6e; 
        margin-bottom: 25px;
        font-size: 1.3em !important;
    }
    
    /* === 側邊欄提示 === */
    .sidebar-hint {
        background-color: #fffbeb;
        border: 2px solid #fcd34d;
        color: #92400e;
        padding: 12px 18px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-size: 1.2em;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* === 載入動畫 === */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.9);
        z-index: 99999;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(5px);
    }
    .loading-content {
        background: white;
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        text-align: center;
        min-width: 320px;
    }
    .loading-text {
        margin-top: 25px;
        color: #0284c7;
        font-weight: bold;
        font-size: 1.8em;
        animation: blink 1.5s infinite;
    }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

    /* === 紅框輸入區樣式 === */
    .stChatInput {
        position: fixed !important;
        bottom: 20px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 90% !important;
        max-width: 800px !important;
        z-index: 1000 !important;
        padding-bottom: 20px !important; 
    }
    
    [data-testid="stChatInput"] {
        border: 3px solid #ef4444 !important; 
        border-radius: 25px !important;
        background-color: #fff0f0 !important; 
        padding: 10px !important;
        box-shadow: 0 -5px 20px rgba(0,0,0,0.1) !important;
    }
    
    /* 增加主頁面底部的留白 */
    .main .block-container {
        padding-bottom: 250px !important; 
    }

    /* === 側邊欄按鈕文字修正：從「病人基本資料設定」改為「基本資料設定」 === */
    [data-testid="stSidebarCollapsedControl"]::after {
        content: "基本資料設定"; /* 修改處 */
        margin-left: 8px;
        font-weight: bold;
        color: #0284c7;
        font-size: 1.2rem;
        vertical-align: middle;
    }
    
    /* 手機版適配 */
    @media (max-width: 640px) {
        h1 { font-size: 2.4rem !important; }
        h2 { font-size: 1.8rem !important; }
        h3 { font-size: 1.5rem !important; }
        .stButton>button { font-size: 1.2rem !important; height: 3.8em; }
        /* 手機版側邊欄按鈕文字 */
        [data-testid="stSidebarCollapsedControl"]::after { content: "基本資料設定"; font-size: 1rem; }
        .stChatInput { bottom: 10px !important; width: 95% !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 專業指引知識庫 ---
GUIDELINE_CONTEXT = """
【核心營養指引準則】
請綜合參考以下權威文獻進行判斷：

1. **KDOQI 2020 (Clinical Practice Guideline for Nutrition in CKD)**:
   - **蛋白質 (未透析)**: 
     - 無糖尿病: 建議低蛋白飲食 0.55-0.60 g/kg/day。
     - 有糖尿病: 建議 0.6-0.8 g/kg/day (需嚴格控糖)。
   - **蛋白質 (透析)**: 建議 1.0-1.2 g/kg/day。
   - **鈉**: 強烈建議限制 < 2.3 g/day。
   - **鉀/磷**: 需依血值調整，通常需限制高鉀高磷食物。

2. **Nutr Sci J 2022 (台灣)**:
   - 加工食品無機磷吸收率 100%，應絕對避免。
   
3. **AJKD 2024**:
   - 維生素 A/E 不建議常規補充。
   - 綜合維他命需個別評估。

【判斷邏輯與矛盾處理 (AI Override)】
- **你的判斷為最終依據 (AI Override)**。
- 如果系統初步判斷為綠燈，但你發現成分中有嚴重隱患（如糖尿病患吃到精緻糖、透析患吃到高鉀果乾、加工食品含無機磷），請務必將 `final_risk_level` 改為 "red" 或 "yellow"。
- **標題要求**：若判定為紅燈，`summary_title` 必須明確寫出「紅燈（不建議食用）！」。
"""

# --- 4. 風險關鍵字資料庫 ---
RISK_KEYWORDS = {
    "inorganic_phosphate": [
        "磷酸", "偏磷酸", "焦磷酸", "三聚磷酸", "polyphosphate", 
        "膨鬆劑", "泡打粉", "品質改良劑"
    ],
    "high_risk_ingredients": [
        "氯化鉀", "低鈉鹽", "代鹽", "魚漿", "貢丸", "香腸", "火腿"
    ],
    "high_potassium_food": [
        "濃縮果汁", "堅果", "花生", "巧克力", "可可", "咖啡", "椰子", "香蕉", "奇異果", 
        "果乾", "乾燥水果", "raisin", "dried fruit"
    ],
    "dairy_warning": [ 
        "鮮奶", "牛奶", "牛乳", "奶粉", "起司", "乳酪", "優格", "milk", "cheese", "yogurt"
    ],
    "high_sugar": [
        "砂糖", "果糖", "玉米糖漿", "精緻糖", "syrup", "sugar", "蜂蜜", "honey", "麥芽糖"
    ]
}

# --- 5. Session State 初始化 ---
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        "calories": 0.0, "protein": 0.0, "sodium": 0.0, 
        "potassium": 0.0, "phosphorus": 0.0, "ingredients": ""
    }
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'ai_advice' not in st.session_state:
    st.session_state.ai_advice = None
if 'context_chat_history' not in st.session_state: 
    st.session_state.context_chat_history = []
if 'general_chat_history' not in st.session_state: 
    st.session_state.general_chat_history = []

# --- 6. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 基本資料設定") # 這裡也同步修改
    
    api_key = ""
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="請輸入 API Key")
    
    st.divider()
    st.subheader("👤 治療狀態")
    
    treatment_status = st.radio("目前治療狀態", ["未透析 (慢性腎臟病)", "透析"], index=0)
    
    patient_status_desc = ""
    if treatment_status == "透析":
        dialysis_type = st.radio("透析種類", ["血液透析", "腹膜透析"])
        st.info("💡 KDOQI 2020：透析病患需攝取足夠蛋白質 (1.0-1.2 g/kg)。")
        patient_status_desc = f"透析病患 - {dialysis_type}"
    else:
        ckd_stage_opt = st.selectbox("請選擇分期", [
            "第一期 (GFR ≥ 90)", "第二期 (GFR 60-89.9)", "第三期 3a (GFR 45-59.9)",
            "第三期 3b (GFR 30-44.9)", "第四期 (GFR 15-29.9)", "第五期 (GFR < 15)"
        ])
        patient_status_desc = f"慢性腎臟病 (未透析) - {ckd_stage_opt}"

    st.session_state.patient_status_desc = patient_status_desc

    st.divider()
    st.subheader("➕ 共病症")
    c1, c2 = st.columns(2)
    with c1:
        has_dm = st.checkbox("糖尿病", help="將嚴格檢查精緻糖分")
        has_htn = st.checkbox("高血壓", help="嚴格把關鈉含量")
    with c2:
        has_gout = st.checkbox("痛風", help="注意高普林")
        has_dl = st.checkbox("高血脂", help="注意脂肪類型")
    
    comorbidities = []
    if has_dm: comorbidities.append("糖尿病")
    if has_htn: comorbidities.append("高血壓")
    if has_gout: comorbidities.append("痛風")
    if has_dl: comorbidities.append("高血脂")
    
    st.session_state.comorbidity_desc = "、".join(comorbidities) if comorbidities else "無"

# --- 7. 核心邏輯函數 ---

def analyze_food_rules():
    """本地規則分析 (初步篩檢)"""
    st.session_state.ai_advice = None
    st.session_state.context_chat_history = []
    
    data = st.session_state.form_data
    ingredients = data["ingredients"]
    
    # 無數據處理
    if data["calories"] == 0 and data["sodium"] == 0 and data["protein"] == 0:
        st.session_state.analysis_result = {
            "risk_level": "unknown",
            "findings": {"inorganic_p": [], "high_k_food": [], "dairy": [], "high_sugar": []},
            "summary": "⚠️ 未偵測到數值，無法進行紅綠燈判斷。請直接點擊下方「✨ 呼叫 AI 營養師」進行定性分析。"
        }
        return 

    findings = {
        "inorganic_p": [], "high_k_food": [], "dairy": [], "high_sugar": [],
        "sodium_warning": False, "p_ratio_warning": None, "k_level": None
    }
    
    for kw in RISK_KEYWORDS["inorganic_phosphate"]:
        if kw in ingredients: findings["inorganic_p"].append(kw)
    for kw in RISK_KEYWORDS["high_potassium_food"]:
        if kw in ingredients: findings["high_k_food"].append(kw)
    for kw in RISK_KEYWORDS["dairy_warning"]:
        if kw in ingredients: findings["dairy"].append(kw)
    for kw in RISK_KEYWORDS["high_sugar"]:
        if kw in ingredients: findings["high_sugar"].append(kw)
        
    if data["phosphorus"] > 0 and data["protein"] > 0:
        ratio = data["phosphorus"] / data["protein"]
        if ratio > 12: findings["p_ratio_warning"] = round(ratio, 1)
    
    if data["potassium"] > 0:
        if data["potassium"] > 300: findings["k_level"] = "High"
        elif data["potassium"] >= 200: findings["k_level"] = "Medium"
        else: findings["k_level"] = "Low"
        
    if data["sodium"] > 200: findings["sodium_warning"] = True
    
    risk_level = "green"
    is_diabetic_risk = "糖尿病" in st.session_state.comorbidity_desc and len(findings["high_sugar"]) > 0

    if (data["sodium"] > 400 or 
        len(findings["inorganic_p"]) > 0 or 
        "氯化鉀" in ingredients or 
        findings["k_level"] == "High" or
        is_diabetic_risk):
        risk_level = "red"
    elif (data["sodium"] > 200 or 
          len(findings["high_k_food"]) > 0 or 
          len(findings["dairy"]) > 0 or
          len(findings["high_sugar"]) > 0):
        risk_level = "yellow"
        
    if risk_level == "red":
        summary = "紅燈（不建議食用）！"
        reasons = []
        if len(findings["inorganic_p"]) > 0: reasons.append("含磷酸鹽添加物")
        if data["sodium"] > 400: reasons.append("鈉含量過高")
        if is_diabetic_risk: reasons.append("糖尿病患者不宜食用高糖")
        if reasons: summary += "原因：" + "、".join(reasons)
    elif risk_level == "yellow":
        summary = "需注意！建議淺嚐。"
    else:
        summary = "綠燈通行！數值合宜。"
        
    st.session_state.analysis_result = {
        "risk_level": risk_level, "findings": findings, "summary": summary
    }

def extract_data_from_image(uploaded_file, api_key):
    """OCR 與 產品辨識"""
    if not api_key:
        st.error("⚠️ 請先輸入 API Key 才能使用 AI 功能")
        return False

    try:
        image_bytes = uploaded_file.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """
        任務：分析圖片中的食品資訊。
        1. 搜尋營養標示：若有表格，提取數值。
        2. 產品辨識：若無標示，讀取產品名稱與主要成分。
           - 若確認為「無糖茶」或「水」，數值可填 0。
           - 若為其他食品且無標示，數值填 0，但必須在 ingredients 中詳列辨識出的成分。
        
        回傳 JSON (無 markdown):
        {
            "calories": float,
            "protein": float,
            "sodium": float,
            "potassium": float (無則0),
            "phosphorus": float (無則0),
            "ingredients": string
        }
        """

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": uploaded_file.type, "data": base64_image}}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            raw_text = result['candidates'][0]['content']['parts'][0]['text']
            extracted_data = json.loads(raw_text)
            st.session_state.form_data.update(extracted_data)
            
            st.session_state.analysis_result = None
            st.session_state.ai_advice = None
            st.session_state.context_chat_history = []
            return True
        else:
            st.error(f"圖片辨識失敗: {response.status_code}")
            return False

    except Exception as e:
        st.error(f"發生錯誤: {str(e)}")
        return False

def call_gemini_deep_analysis(prompt):
    """AI 深度分析"""
    if not api_key:
        st.error("⚠️ 請先輸入 API Key 才能呼叫 AI")
        return None

    patient_status = st.session_state.get("patient_status_desc", "未設定")
    comorbidities = st.session_state.get("comorbidity_desc", "無")
    
    current_system_result = "無"
    if st.session_state.analysis_result:
        current_system_result = f"{st.session_state.analysis_result['risk_level']} ({st.session_state.analysis_result['summary']})"

    system_instruction = f"""
    你是一位台灣專業的腎臟科專科營養師。
    {GUIDELINE_CONTEXT}
    
    【病患檔案】：
    - 腎臟狀態：{patient_status}
    - 共病症：{comorbidities}
    
    【系統初步規則判斷】：{current_system_result}
    
    任務：
    1. 進行深度營養評估。
    2. **最終裁決 (Override)**：
       - 如果你認為該食品「不建議食用」，請務必將 `final_risk_level` 設為 "red"，並且 `summary_title` 必須為 **"紅燈（不建議食用）！"**。
       - 你的判斷將直接覆蓋系統的紅綠燈，請嚴格把關。
    3. 請回傳 JSON 格式。
    
    JSON 結構：
    {{
        "final_risk_level": "green" | "yellow" | "red",
        "summary_title": "簡短標題 (紅燈時請填：紅燈（不建議食用）！)",
        "detailed_analysis": "詳細分析內容 (Markdown)",
        "serving_suggestion": "食用建議 (Markdown)"
    }}
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "generationConfig": {"response_mime_type": "application/json"}
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
        return None
    except Exception as e:
        st.error(f"連線錯誤: {str(e)}")
        return None

def call_gemini_chat(prompt, chat_history_key=None):
    if not api_key:
        st.error("⚠️ 請先輸入 API Key")
        return None
    
    patient_status = st.session_state.get("patient_status_desc", "未設定")
    comorbidities = st.session_state.get("comorbidity_desc", "無")
    
    system_instruction = f"""
    你是一位台灣專業的腎臟科專科營養師。
    {GUIDELINE_CONTEXT}
    【病患檔案】：{patient_status}，共病症：{comorbidities}。
    請給予簡短、溫暖且專業的建議。
    """
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={api_key}"
        contents = []
        if chat_history_key and chat_history_key in st.session_state:
             for msg in st.session_state[chat_history_key]:
                 role = "user" if msg["role"] == "user" else "model"
                 contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})
        
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_instruction}]}
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        return None
    except Exception as e:
        st.error(f"連線錯誤: {str(e)}")
        return None

# --- 8. UI 主畫面佈局 ---

tab1, tab2 = st.tabs(["📊 食品掃描與分析", "💬 AI 諮詢室"])

with tab1:
    # 修改為更簡潔的提示文字
    st.markdown("""
    <div class='sidebar-hint'>
        👉 <b>請點擊左上角箭頭 ( > )</b> 展開側邊欄，設定<b>【基本資料】</b>與<b>【共病症】</b>以獲得精準分析
    </div>
    """, unsafe_allow_html=True)

    status_desc = st.session_state.get("patient_status_desc", "未設定")
    comor_desc = st.session_state.get("comorbidity_desc", "無")
    
    st.markdown(f"""
    <div class='status-card'>
        <b>當前設定對象：</b>{status_desc}<br>
        <b>共病症：</b>{comor_desc}
    </div>
    """, unsafe_allow_html=True)

    # 圖片上傳區
    with st.expander("📸 圖片辨識 (上傳營養標示或產品正面)", expanded=True):
        uploaded_file = st.file_uploader("上傳照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            col_img, col_btn = st.columns([1, 2])
            with col_img:
                st.image(uploaded_file, caption="預覽圖片", use_container_width=True)
            with col_btn:
                if st.button("🚀 開始 AI 讀圖", type="primary"):
                    placeholder = st.empty()
                    placeholder.markdown("""
                        <div class='loading-overlay'>
                            <div class='loading-content'>
                                <img src='https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif' width='150'>
                                <div class='loading-text'>AI 正在讀取圖片中...</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    success = extract_data_from_image(uploaded_file, api_key)
                    placeholder.empty() # 清除動畫
                    
                    if success:
                        st.success("讀取完成！")
                    else:
                        st.error("讀取失敗。")
                else:
                    st.info("AI 將自動讀取數值或辨識產品名稱...")

    # 數據確認區
    st.subheader("📝 確認數據 / 產品資訊")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.form_data["calories"] = st.number_input("熱量", value=float(st.session_state.form_data["calories"]))
        st.session_state.form_data["sodium"] = st.number_input("鈉", value=float(st.session_state.form_data["sodium"]))
        st.session_state.form_data["phosphorus"] = st.number_input("磷", value=float(st.session_state.form_data["phosphorus"]))
    with c2:
        st.session_state.form_data["protein"] = st.number_input("蛋白質", value=float(st.session_state.form_data["protein"]))
        st.session_state.form_data["potassium"] = st.number_input("鉀", value=float(st.session_state.form_data["potassium"]))
    
    st.session_state.form_data["ingredients"] = st.text_area("成分 / 產品名稱", value=st.session_state.form_data["ingredients"], height=80)

    st.markdown("---")
    
    # 執行規則分析按鈕
    if st.button("🔍 執行分析 (規則判斷)", type="primary", use_container_width=True):
        analyze_food_rules()
        st.rerun()

    # 顯示結果區
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        
        risk_level = res['risk_level']
        display_summary = res['summary']
        
        if risk_level == "unknown":
            st.info(f"### {display_summary}") 
        elif risk_level == "red":
            st.error(f"### {display_summary}") 
        elif risk_level == "yellow":
            st.warning(f"### {display_summary}") 
        elif risk_level == "green":
            st.success(f"### {display_summary}") 

        if res['findings']['inorganic_p']:
            st.error(f"⚠️ 檢出無機磷：{', '.join(res['findings']['inorganic_p'])}")
        if res['findings']['dairy']:
            st.warning(f"🥛 檢出乳製品：{', '.join(res['findings']['dairy'])}")
        if res['findings']['high_sugar']:
            st.warning(f"🍬 檢出高糖成分：{', '.join(res['findings']['high_sugar'])}")
        
        # AI 深度解析按鈕與顯示
        if not st.session_state.ai_advice:
            if st.button("✨ 呼叫 AI 營養師深度解析 (推薦)"):
                placeholder = st.empty()
                placeholder.markdown("""
                    <div class='loading-overlay'>
                        <div class='loading-content'>
                            <img src='https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif' width='150'>
                            <div class='loading-text'>AI 營養師正在評估中...</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                prompt = f"分析食品: {st.session_state.form_data}. 若數值為0，請根據產品名稱與成分描述進行定性評估。"
                ai_result = call_gemini_deep_analysis(prompt)
                placeholder.empty() 

                if ai_result:
                    st.session_state.ai_advice = ai_result
                    st.session_state.analysis_result['risk_level'] = ai_result['final_risk_level']
                    st.session_state.analysis_result['summary'] = ai_result['summary_title']
                    st.rerun() 
        else:
            # 顯示 AI 詳細分析
            st.markdown("### 👩‍⚕️ AI 營養師深度報告")
            st.markdown(st.session_state.ai_advice['detailed_analysis'])
            st.info(f"💡 **食用建議**：{st.session_state.ai_advice['serving_suggestion']}")
            
            # 追問
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; margin-top: 20px; margin-bottom: 10px; font-weight: bold; color: #6b7280;">
                👇 還有疑問嗎？請在下方紅框輸入...
            </div>
            """, unsafe_allow_html=True)

            # 顯示歷史對話
            for msg in st.session_state.context_chat_history:
                st.chat_message(msg["role"]).write(msg["content"])

            if follow_up_q := st.chat_input("針對此食品有疑問嗎？ (例如：我可以只吃一半嗎？)", key="follow_up_chat"):
                st.session_state.context_chat_history.append({"role":"user", "content":follow_up_q})
                st.chat_message("user").write(follow_up_q)
                
                placeholder = st.empty()
                placeholder.markdown("""
                    <div class='loading-overlay'>
                        <div class='loading-content'>
                            <img src='https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif' width='150'>
                            <div class='loading-text'>AI 正在思考中...</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                context = json.dumps(st.session_state.ai_advice, ensure_ascii=False)
                full_prompt = f"關於剛剛分析的食品報告：{context}。使用者追問：{follow_up_q}"
                ans = call_gemini_chat(full_prompt, "context_chat_history")
                
                placeholder.empty()
                
                if ans:
                    st.session_state.context_chat_history.append({"role":"assistant", "content":ans})
                    st.rerun() # 重新整理以顯示新對話

with tab2:
    st.markdown("### 💬 AI 營養諮詢室 (一般問答)")
    status_desc = st.session_state.get("patient_status_desc", "未設定")
    comor_desc = st.session_state.get("comorbidity_desc", "無")
    st.info(f"當前諮詢身份：{status_desc}")
    if comor_desc != "無": st.warning(f"⚠️ 共病考量：{comor_desc}")

    for msg in st.session_state.general_chat_history:
        st.chat_message(msg["role"]).write(msg["content"])
        
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; margin-bottom: 10px; font-weight: bold; color: #6b7280;">
        👇 請在下方紅框輸入您的問題...
    </div>
    """, unsafe_allow_html=True)
    
    # === 確保這頁的輸入框也有紅框樣式 ===
    if q := st.chat_input("請問營養師...", key="general_chat_input"):
        st.session_state.general_chat_history.append({"role":"user", "content":q})
        st.chat_message("user").write(q)
        
        placeholder = st.empty()
        placeholder.markdown("""
            <div class='loading-overlay'>
                <div class='loading-content'>
                    <img src='https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif' width='150'>
                    <div class='loading-text'>AI 正在思考中...</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        ans = call_gemini_chat(q, "general_chat_history")
        placeholder.empty()

        if ans:
            st.session_state.general_chat_history.append({"role":"assistant", "content":ans})
            st.rerun()