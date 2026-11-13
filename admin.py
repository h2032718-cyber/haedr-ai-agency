import streamlit as st
import requests
import json
import base64

st.set_page_config(page_title="لوحة إدارة الوكالة", page_icon="⚙️", layout="wide")
st.title("⚙️ لوحة إدارة المتاجر الذكية")

# إعدادات GitHub
TOKEN = st.secrets.get("GITHUB_TOKEN")
REPO = "h2032718-cyber/haedr-ai-agency"
API_BASE = f"https://api.github.com/repos/{REPO}"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# دوال GitHub
def get_files_in_data():
    res = requests.get(f"{API_BASE}/contents/data", headers=headers)
    if res.status_code == 200:
        return [f['name'].replace('.json', '') for f in res.json() if f['name'].endswith('.json')]
    return []

def get_file_data(filename):
    res = requests.get(f"{API_BASE}/contents/data/{filename}.json", headers=headers)
    if res.status_code == 200:
        content = base64.b64decode(res.json()['content']).decode('utf-8')
        return json.loads(content), res.json()['sha']
    return None, None

def save_file_data(filename, data, sha):
    content = json.dumps(data, ensure_ascii=False, indent=2)
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {"message": f"تحديث {filename}", "content": encoded, "sha": sha}
    res = requests.put(f"{API_BASE}/contents/data/{filename}.json", headers=headers, data=json.dumps(payload))
    return res.status_code == 200

if not TOKEN:
    st.error("⚠️ يرجى إضافة المفتاح السري GITHUB_TOKEN في إعدادات التطبيق (Secrets).")
    st.stop()

# جلب المتاجر
stores = get_files_in_data()
if not stores:
    st.warning("لا توجد متاجر. يرجى إضافة ملف بيانات أولاً.")
    st.stop()

# اختيار المتجر
selected_store = st.sidebar.selectbox("اختر المتجر للإدارة:", stores)
st.sidebar.info(f"أنت تدير الآن: **{selected_store}**")

data, sha = get_file_data(selected_store)
if not data:
    st.error("تعذر جلب بيانات المتجر.")
    st.stop()

# إنشاء التبويبات
tab1, tab2, tab3 = st.tabs(["🏪 معلومات المتجر", "🛍️ الخدمات/المنتجات", "🧠 أسئلة البوت"])

# --- التبويب الأول: معلومات المتجر ---
with tab1:
    st.header("تعديل معلومات المتجر الأساسية")
    info = data.get("store_info", {})
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("اسم المتجر", info.get("name", ""))
        whatsapp = st.text_input("رقم الواتساب (بصيغة دولية بدون +)", info.get("whatsapp", ""))
        address = st.text_input("العنوان", info.get("address", ""))
    with col2:
        open_hour = st.number_input("ساعة الفتح (0-23)", min_value=0, max_value=23, value=int(info.get("openHour", 8)))
        close_hour = st.number_input("ساعة الإغلاق (0-23)", min_value=0, max_value=23, value=int(info.get("closeHour", 20)))
        closed_day = st.selectbox("يوم الإغلاق", options=[0,1,2,3,4,5,6], index=int(info.get("closedDay", 5)), format_func=lambda x: ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"][x])
    
    if st.button("💾 حفظ معلومات المتجر", type="primary"):
        data["store_info"] = {
            "name": name, "whatsapp": whatsapp, "address": address,
            "openHour": open_hour, "closeHour": close_hour, "closedDay": closed_day,
            "description": info.get("description", "")
        }
        if save_file_data(selected_store, data, sha):
            st.success("✅ تم الحفظ بنجاح!")
            st.rerun()

# --- التبويب الثاني: الخدمات/المنتجات ---
with tab2:
    st.header("إدارة الخدمات التي تظهر في الواجهة")
    products = data.get("products", [])
    
    edited_products = st.data_editor(
        products,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("اسم الخدمة", required=True),
            "desc": st.column_config.TextColumn("الوصف", required=True),
            "image": st.column_config.TextColumn("رابط الصورة"),
            "msg": st.column_config.TextColumn("رسالة الواتساب")
        },
        key="prod_editor"
    )
    
    if st.button("💾 حفظ الخدمات", type="primary"):
        data["products"] = edited_products
        if save_file_data(selected_store, data, sha):
            st.success("✅ تم حفظ الخدمات بنجاح!")
            st.rerun()

# --- التبويب الثالث: أسئلة البوت ---
with tab3:
    st.header("إدارة أسئلة وأجوبة البوت الذكي")
    qa = data.get("qa_data", [])
    
    edited_qa = st.data_editor(
        qa,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "q": st.column_config.TextColumn("السؤال", required=True, width="large"),
            "a": st.column_config.TextColumn("الإجابة", required=True, width="large")
        },
        key="qa_editor"
    )
    
    if st.button("💾 حفظ أسئلة البوت", type="primary"):
        data["qa_data"] = edited_qa
        if save_file_data(selected_store, data, sha):
            st.success("✅ تم حفظ الأسئلة بنجاح! البوت سيتحدث فوراً.")
            st.rerun()
