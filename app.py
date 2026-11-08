# import streamlit as st

# st.title("Hello Streamlit 👋")
# st.write("Streamlit 앱이 정상적으로 실행되고 있습니다.")


# Anaconda Prompt

# conda activate py310

# (py310) C:\Users\HPE>cd C:\Users\HPE\Desktop\langchain-web-chatbot-edu-2026-main\langchain-web-chatbot-edu-2026-main

# (py310) C:\Users\HPE\Desktop\langchain-web-chatbot-edu-2026-main\langchain-web-chatbot-edu-2026-main>streamlit run app.py

# http://localhost:8501/


import streamlit as st

st.header("입력 위젯 데모")

name = st.text_input("이름을 입력하세요")
age = st.number_input("나이", min_value=0, max_value=120, value=25)
lang = st.selectbox("언어 선택", ["Python", "R", "C++"])
submit = st.button("확인")

if submit:
    st.success(f"{name}님은 {age}세이며, {lang}을(를) 사용합니다.")


import pandas as pd
import numpy as np

st.header("출력 요소 예제")

data = pd.DataFrame({
    'x': np.arange(1, 6),
    'y': np.random.randint(1, 100, 5)
})

st.dataframe(data)
st.bar_chart(data.set_index('x'))


# (base) C:\Users\HPE>cd C:\Users\HPE\Desktop\langchain-web-chatbot-edu-2026-main\langchain-web-chatbot-edu-2026-main

# (base) C:\Users\HPE\Desktop\langchain-web-chatbot-edu-2026-main\langchain-web-chatbot-edu-2026-main>cd  BackgroundRemoval

# (base) C:\Users\HPE\Desktop\langchain-web-chatbot-edu-2026-main\langchain-web-chatbot-edu-2026-main\BackgroundRemoval>streamlit run bg_remove.py
# 2026-11-08 10:38:09.649 Uvicorn server started on 0.0.0.0:8501

# conda activate py310
# pip list
# cd BackgroundRemoval
# streamlit run bg_remove.py


