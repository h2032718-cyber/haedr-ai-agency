import streamlit as st
from sentence_transformers import SentenceTransformer, util
import requests
import json
import os
from groq import Groq

st.set_page_config(page_title="مساعد المتجر الذكي", page_icon="🤖")
st.title("🤖 المساعد الذكي")
st.write("مرحباً! كيف يمكنني مساعدتك اليوم؟")

# 1. جلب اسم المتجر من الرابط (الافتراضي هو haedr_tech)
query_params = st.query_params
store_id = query_params.get("store", "haedr_tech")

# 2. جلب بيانات المتجر من GitHub
@st.cache_data(ttl=60)
def load_store_data(store):
    url = f"https://raw.githubusercontent.com/h2032718-cyber/haedr-ai-agency/main/data/{store}.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

store_data = load_store_data(store_id)

if not store_data:
    st.error(f"⚠️ لم يتم العثور على بيانات للمتجر: {store_id}")
    st.stop()

qa_data = store_data.get("qa_data", [])
store_info = store_data.get("store_info", {})

# إذا كانت قاعدة البيانات فارغة (مثل حالتنا الآن)
if len(qa_data) == 0:
    st.info("👋 مرحباً! لم يقم مدير المتجر بإضافة أي أسئلة وأجوبة حتى الآن. يرجى العودة لاحقاً أو التواصل عبر الواتساب.")
    st.stop()

# 3. تحميل نموذج البحث (RAG)
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()
questions = [item["q"] for item in qa_data]
question_embeddings = model.encode(questions)

def get_bot_response(message):
    msg_embedding = model.encode(message)
    cos_scores = util.cos_sim(msg_embedding, question_embeddings)[0]
    best_idx = cos_scores.argmax()
    best_score = cos_scores[best_idx].item()

    if best_score > 0.55:
        retrieved_answer = qa_data[best_idx]["a"]
        try:
            api_key = st.secrets["GROQ_API_KEY"]
            client = Groq(api_key=api_key)
            
            store_name = store_info.get("name", "المتجر")
            prompt = f"أنت مساعد ودود لمتجر اسمه ({store_name}). أجب على سؤال الزبون بأسلوب طبيعي ومختصر بناءً على هذه المعلومة فقط: {retrieved_answer}\n\nإذا كانت المعلومة لا تجيب على السؤال، قل: 'عذراً، لا أملك هذه المعلومة.'\n\nسؤال الزبون: {message}"
            
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return chat_completion.choices[0].message.content
        except Exception:
            return retrieved_answer
    else:
        return "عذراً، لا أملك معلومات كافية عن هذا السؤال. يرجى التواصل معنا عبر واتساب للتفاصيل."

# 4. واجهة المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("اكتب سؤالك هنا..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = get_bot_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
