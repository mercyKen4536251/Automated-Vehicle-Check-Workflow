import streamlit as st
import sys
import os

# 添加项目根目录到路径（app.py 现在在 pages/ 下）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src import config_manager as cm
from src import data_manager as dm

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AVCW - Automated Vehicle Check Workflow",
    page_icon="🚗",
    layout="wide"
)

# ==================== 页面地址 ====================
page_0 = "manage\\config.py"
page_1 = "manage\\prompt.py"
page_2 = "manage\\ref_gallery.py"
page_3 = "manage\\test_cases.py"
page_4 = "test\\run_test.py"
page_5 = "test\\task_queue.py"
page_6 = "test\\result.py"

pages = {
    "Manage": [
        st.Page(page_0, title="配置管理"),
        st.Page(page_1, title="提示词管理"),
        st.Page(page_2, title="参考图管理"),
        st.Page(page_3, title="测试用例管理"),
    ],
    "Test": [
        st.Page(page_4, title="执行测试"),
        st.Page(page_5, title="任务队列"),
        st.Page(page_6, title="结果面板"),
    ],
}

# ==================== 配置导航栏(top) ====================
pg = st.navigation(pages, position="top")
pg.run()