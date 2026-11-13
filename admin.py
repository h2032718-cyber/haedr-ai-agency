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

# جلب المتاجر واختيار المتجر
stores = get_files_in_data()
if not stores:
    st.warning("لا توجد متاجر. يرجى إضافة ملف بيانات أولاً.")
    st.stop()

selected_store = st.sidebar.selectbox("اختر المتجر للإدارة:", stores)
st.sidebar.info(f"أنت تدير الآن: **{selected_store}**")

data, sha = get_file_data(selected_store)
if not data:
    st.error("تعذر جلب بيانات المتجر.")
    st.stop()

# إنشاء التبويبات
tab1, tab2, tab3 = st.tabs(["🏪 معلومات المتجر", "🛍️ الخدمات/المنتجات", "🧠 أسئلة البوت"])

# --- التبويب الأول: معلومات المتجر (نموذج) ---
with tab1:
    st.header("تعديل معلومات المتجر الأساسية")
    info = data.get("store_info", {})
    
    with st.form("store_info_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("اسم المتجر", info.get("name", ""))
            whatsapp = st.text_input("رقم الواتساب (بصيغة دولية بدون +)", info.get("whatsapp", ""))
            address = st.text_input("العنوان", info.get("address", ""))
        with col2:
            open_hour = st.number_input("ساعة الفتح (0-23)", min_value=0, max_value=23, value=int(info.get("openHour", 8)))
            close_hour = st.number_input("ساعة الإغلاق (0-23)", min_value=0, max_value=23, value=int(info.get("closeHour", 20)))
            closed_day = st.selectbox("يوم الإغلاق", options=[0,1,2,3,4,5,6], index=int(info.get("closedDay", 5)), format_func=lambda x: ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"][x])
        
        submitted = st.form_submit_button("💾 حفظ معلومات المتجر")
        if submitted:
            data["store_info"] = {
                "name": name, "whatsapp": whatsapp, "address": address,
                "openHour": open_hour, "closeHour": close_hour, "closedDay": closed_day,
                "description": info.get("description", "")
            }
            if save_file_data(selected_store, data, sha):
                st.success("✅ تم الحفظ بنجاح!")
                st.rerun()

# --- التبويب الثاني: الخدمات (نموذج) ---
with tab2:
    st.header("إدارة الخدمات التي تظهر في الواجهة")
    products = data.get("products", [])
    
    with st.form("add_product_form", clear_on_submit=True):
        st.subheader("إضافة خدمة جديدة")
        new_name = st.text_input("اسم الخدمة")
        new_desc = st.text_input("الوصف القصير")
        new_image = st.text_input("رابط الصورة (اختياري)")
        new_msg = st.text_input("رسالة الواتساب")
        
        if st.form_submit_button("➕ إضافة الخدمة"):
            if new_name and new_desc and new_msg:
                products.append({"name": new_name, "desc": new_desc, "image": new_image, "msg": new_msg})
                data["products"] = products
                if save_file_data(selected_store, data, sha):
                    st.success(f"✅ تمت إضافة الخدمة: {new_name}")
                    st.rerun()
            else:
                st.error("الرجاء ملء جميع الحقول المطلوبة.")
    
    st.divider()
    st.subheader("الخدمات الحالية")
    for i, p in enumerate(products):
        with st.expander(f"{p['name']} - {p['desc']}"):
            st.write(f"**رسالة الواتساب:** {p['msg']}")
            if st.button(f"🗑️ حذف {p['name']}", key=f"del_prod_{i}"):
                products.pop(i)
                data["products"] = products
                if save_file_data(selected_store, data, sha):
                    st.warning(f"تم حذف الخدمة: {p['name']}")
                    st.rerun()

# --- التبويب الثالث: أسئلة البوت (نموذج) ---
with tab3:
    st.header("إدارة أسئلة وأجوبة البوت الذكي")
    qa = data.get("qa_data", [])
    
    with st.form("add_qa_form", clear_on_submit=True):
        st.subheader("إضافة سؤال جديد")
        new_q = st.text_input("السؤال")
        new_a = st.text_input("الإجابة")
        
        if st.form_submit_button("➕ إضافة السؤال"):
            if new_q and new_a:
                qa.append({"q": new_q, "a": new_a})
                data["qa_data"] = qa
                if save_file_data(selected_store, data, sha):
                    st.success(f"✅ تمت إضافة السؤال: {new_q}")
                    st.rerun()
            else:
                st.error("الرجاء ملء السؤال والإجابة.")
    
    st.divider()
    st.subheader("الأسئلة الحالية")
    for i, item in enumerate(qa):
        with st.expander(f"❓ {item['q']}"):
            st.write(f"**الإجابة:** {item['a']}")
            if st.button(f"🗑️ حذف", key=f"del_qa_{i}"):
                qa.pop(i)
                data["qa_data"] = qa
                if save_file_data(selected_store, data, sha):
                    st.warning("تم حذف السؤال.")
                    st.rerun()
