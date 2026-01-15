import streamlit as st
import sys
import os
import requests
import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src import data_manager as dm

# ==================== 配置 ====================
BACKEND_URL = "http://localhost:8000"
API_TIMEOUT = 30  # API 请求超时时间（秒）
MAX_CONCURRENT_TASKS = 3  # 最大并发任务数

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_test_cases_cached():
    return dm.get_test_cases()

def check_backend_connection():
    """
    检查后端连接
    
    Check backend connection
    
    Returns:
        bool: 是否连接成功
    """
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def get_running_tasks_count():
    """
    获取运行中的任务数量
    
    Get running tasks count
    
    Returns:
        int: 运行中的任务数量
    """
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/test/tasks?status=running&limit=10",
            timeout=5
        )
        if response.status_code == 200:
            return len(response.json().get("tasks", []))
    except:
        pass
    return 0

# ==================== 页面标题 ====================
st.header("🚀 运行中心")
st.markdown("---")

# 加载数据
cases = load_test_cases_cached()

if cases.empty:
    st.warning("⚠️ 暂无测试用例，请前往【测试用例管理】页面添加。")
    st.stop()

# ==================== 检查后端连接 ====================
backend_available = check_backend_connection()

if not backend_available:
    st.error("❌ 无法连接到后端服务")
    st.info("💡 请确保后端已启动：`python start.py` 或 `uvicorn backend.main:app --port 8000`")
    st.stop()

# ==================== 模块1: 测试用例选择 ====================
st.info(f"📊 共 **{len(cases)}** 条测试用例，请筛选并勾选要测试的用例")

with st.container(border=True):
    # ========== 筛选器 ==========
    col_car, col_type, col_tag = st.columns([1, 1, 1])
    
    # 获取筛选选项
    car_options = cases["car"].unique().tolist()
    type_options = cases["case_type"].unique().tolist()
    tag_options = cases["problem_tag"].dropna().unique().tolist()
    tag_options = [t for t in tag_options if t]  # 过滤空值
    
    with col_car:
        filter_cars = st.multiselect(
            "车系",
            options=car_options,
            default=[],
            placeholder="全部车系",
            key="filter_car"
        )
    
    with col_type:
        filter_types = st.multiselect(
            "类型",
            options=type_options,
            default=[],
            placeholder="全部类型",
            key="filter_type"
        )
    
    with col_tag:
        # 如果只选了goodcase，禁用标签筛选
        only_goodcase = filter_types == ["goodcase"]
        filter_tags = st.multiselect(
            "问题标签",
            options=tag_options,
            default=[],
            placeholder="全部标签" if not only_goodcase else "goodcase无标签",
            disabled=only_goodcase,
            key="filter_tag"
        )
    
    # ========== 应用筛选 ==========
    filtered_cases = cases.copy()
    
    if filter_cars:
        filtered_cases = filtered_cases[filtered_cases["car"].isin(filter_cars)]
    
    if filter_types:
        filtered_cases = filtered_cases[filtered_cases["case_type"].isin(filter_types)]
    
    if filter_tags and not only_goodcase:
        filtered_cases = filtered_cases[filtered_cases["problem_tag"].isin(filter_tags)]
    
    # 降序展示
    cases_sorted = filtered_cases.iloc[::-1].reset_index(drop=True)
    
    st.caption(f"筛选后共 **{len(cases_sorted)}** 条用例")
    
    # ========== 表格展示 ==========
    if cases_sorted.empty:
        st.warning("⚠️ 没有符合筛选条件的用例")
        selected_cases = pd.DataFrame()
    else:
        event = st.dataframe(
            cases_sorted,
            column_config={
                "case_id": st.column_config.TextColumn("ID", width="small"),
                "car": st.column_config.TextColumn("车系", width="medium"),
                "case_type": st.column_config.TextColumn("类型", width="small"),
                "problem_tag": st.column_config.TextColumn("问题标签", width="small"),
                "case_url": st.column_config.LinkColumn("图片", display_text="🔗 Link", width="small"),
            },
            hide_index=True,
            height=350,
            on_select="rerun",
            selection_mode="multi-row",
            key="run_case_selector"
        )
        
        # 获取选中的行
        selected_rows = event.selection.rows
        selected_cases = cases_sorted.iloc[selected_rows] if selected_rows else pd.DataFrame()

    # ========== 显示选择状态 ==========
    st.caption(f"已选择 **{len(selected_cases)}** 条用例")

# ==================== 模块2: 任务提交 ====================

# 获取运行中的任务数
running_count = get_running_tasks_count()

# 判断是否可以提交新任务
can_submit = running_count < MAX_CONCURRENT_TASKS
no_selection = len(selected_cases) == 0

if no_selection:
    st.warning("⚠️ 请勾选需要测试的用例")
elif not can_submit:
    st.warning(f"⚠️ 当前有 {running_count} 个任务正在运行，已达到最大并发数（{MAX_CONCURRENT_TASKS}），请等待任务完成后再提交")

if st.button("▶️ 执行测试", disabled=no_selection or not can_submit, type="primary"):
    # 提交任务到后端
    try:
        case_ids = selected_cases["case_id"].tolist()
        response = requests.post(
            f"{BACKEND_URL}/api/test/submit",
            json={"case_ids": case_ids},
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            st.success(f"""
✅ 任务已提交到后台执行！

- 任务ID: **{result['task_id']}**
- 测试用例数: **{result['total_cases']}**

任务将在后台执行，请前往【任务队列】查看进度。
            """)
            
        else:
            st.error(f"❌ 提交失败: {response.text}")
    except Exception as e:
        st.error(f"❌ 提交失败: {e}")

