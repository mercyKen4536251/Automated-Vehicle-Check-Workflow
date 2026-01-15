import streamlit as st
import sys
import os
import time
import requests
import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src import data_manager as dm

# ==================== 配置 ====================
BACKEND_URL = "http://localhost:8000"

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_test_cases_cached():
    return dm.get_test_cases()

# ==================== 页面标题 ====================
st.header("🚀 运行中心")
st.markdown("---")

# 加载数据
cases = load_test_cases_cached()

if cases.empty:
    st.warning("⚠️ 暂无测试用例，请前往【测试用例管理】页面添加。")
    st.stop()

# ==================== 初始化 session_state ====================
if "selected_case_ids" not in st.session_state:
    st.session_state.selected_case_ids = set()

if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None

if "task_submitted" not in st.session_state:
    st.session_state.task_submitted = False

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
        
        # ========== 累积选择逻辑 ==========
        # 获取当前表格中选中的行
        selected_rows = event.selection.rows
        if selected_rows:
            # 将选中的 case_id 添加到累积集合
            selected_case_ids_in_table = cases_sorted.iloc[selected_rows]["case_id"].tolist()
            st.session_state.selected_case_ids.update(selected_case_ids_in_table)
    
    # ========== 显示累积选择状态 ==========
    st.markdown("---")
    col_status, col_clear = st.columns([3, 1])
    
    with col_status:
        total_selected = len(st.session_state.selected_case_ids)
        if total_selected > 0:
            st.success(f"✅ 已累积选择 **{total_selected}** 条用例（跨筛选条件累积）")
        else:
            st.info("💡 请勾选用例，支持切换筛选条件后继续累积选择")
    
    with col_clear:
        if st.button("🗑️ 清空选择", disabled=total_selected == 0):
            st.session_state.selected_case_ids.clear()
            st.rerun()

st.write("")

# ==================== 模块2: 任务提交与监控 ====================

# 检查后端连接
try:
    health_check = requests.get(f"{BACKEND_URL}/health", timeout=2)
    backend_available = health_check.status_code == 200
except:
    backend_available = False

if not backend_available:
    st.error("❌ 无法连接到后端服务，请确保后端已启动（运行 `python start.py`）")
    st.stop()

# ========== 提交测试 ==========
no_selection = len(st.session_state.selected_case_ids) == 0

if no_selection:
    st.warning("⚠️ 请勾选需要测试的用例")

col_submit, col_cancel = st.columns([3, 1])

with col_submit:
    if st.button("▶️ 执行测试", disabled=no_selection or st.session_state.task_submitted):
        # 提交任务到后端
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/test/submit",
                json={"case_ids": list(st.session_state.selected_case_ids)},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                st.session_state.current_task_id = result["task_id"]
                st.session_state.task_submitted = True
                st.toast(f"✅ 任务已提交！任务ID: {result['task_id']}", icon="✅")
                st.rerun()
            else:
                st.error(f"❌ 提交失败: {response.text}")
        except Exception as e:
            st.error(f"❌ 提交失败: {e}")

with col_cancel:
    if st.button("⏹️ 取消任务", disabled=not st.session_state.task_submitted):
        if st.session_state.current_task_id:
            try:
                response = requests.post(
                    f"{BACKEND_URL}/api/test/cancel/{st.session_state.current_task_id}",
                    timeout=5
                )
                if response.status_code == 200:
                    st.toast("✅ 任务已取消", icon="⏹️")
                    st.session_state.task_submitted = False
                    st.session_state.current_task_id = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 取消失败: {e}")

# ========== 任务监控 ==========
if st.session_state.task_submitted and st.session_state.current_task_id:
    st.markdown("---")
    st.subheader("📊 任务执行状态")
    
    # 创建占位符
    status_container = st.container()
    progress_placeholder = st.empty()
    metrics_placeholder = st.empty()
    
    # 轮询任务状态
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/test/status/{st.session_state.current_task_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            task_status = response.json()
            
            status = task_status["status"]
            progress = task_status["progress"]
            
            # 显示进度条
            if progress["total"] > 0:
                progress_value = progress["completed"] / progress["total"]
                progress_placeholder.progress(
                    progress_value,
                    text=f"进度: {progress['completed']}/{progress['total']}"
                )
            
            # 显示指标
            col1, col2, col3, col4 = metrics_placeholder.columns(4)
            col1.metric("状态", status.upper())
            col2.metric("总数", progress["total"])
            col3.metric("已完成", progress["completed"])
            col4.metric("失败", progress["failed"])
            
            # 显示当前执行的用例
            if progress["current_case_id"]:
                status_container.info(f"🔄 正在执行 Case {progress['current_case_id']}")
            
            # 任务完成
            if status == "completed":
                st.session_state.task_submitted = False
                
                results = task_status["results"]
                correct_count = sum(1 for r in results if r.get("is_correct", False))
                total_count = len(results)
                accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
                
                st.success(f"""
✅ 测试完成！

- 测试总数: **{total_count}**
- 通过数: **{correct_count}**
- 审图准确率: **{accuracy:.1f}%**
- 任务ID: **{st.session_state.current_task_id}**

请前往【结果面板】查看详细结果。
                """)
                
                # 清空选择
                st.session_state.selected_case_ids.clear()
                st.session_state.current_task_id = None
            
            # 任务失败
            elif status == "failed":
                st.session_state.task_submitted = False
                st.error(f"❌ 任务执行失败: {task_status.get('error', '未知错误')}")
                st.session_state.current_task_id = None
            
            # 任务取消
            elif status == "cancelled":
                st.session_state.task_submitted = False
                st.warning("⚠️ 任务已被取消")
                st.session_state.current_task_id = None
            
            # 任务进行中，自动刷新
            elif status in ["pending", "running"]:
                time.sleep(2)
                st.rerun()
        
        else:
            st.error(f"❌ 获取任务状态失败: {response.text}")
            st.session_state.task_submitted = False
    
    except Exception as e:
        st.error(f"❌ 获取任务状态失败: {e}")
        st.session_state.task_submitted = False
