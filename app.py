import streamlit as st
import sys
import os

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import config_manager as cm
from src import data_manager as dm

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AVCW - Automated Vehicle Check Workflow",
    page_icon="🚗",
    layout="wide"
)

# ==================== 页面地址 ====================
page_0 = "pages\\manage\\config.py"
page_1 = "pages\\manage\\prompt.py"
page_2 = "pages\\manage\\ref_gallery.py"
page_3 = "pages\\manage\\test_cases.py"
page_4 = "pages\\test\\run_test.py"
page_5 = "pages\\test\\result.py"

pages = {
    "Manage": [
        st.Page(page_0, title="配置管理"),
        st.Page(page_1, title="提示词管理"),
        st.Page(page_2, title="参考图管理"),
        st.Page(page_3, title="测试用例管理"),
    ],
    "Test": [
        st.Page(page_4, title="执行测试"),
        st.Page(page_5, title="结果面板"),
    ],
}

# ==================== 配置导航栏(top) ====================
pg = st.navigation(pages, position="top")
pg.run()