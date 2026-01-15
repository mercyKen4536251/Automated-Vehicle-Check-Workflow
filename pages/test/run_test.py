import streamlit as st
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src import data_manager as dm
from src import workflow_engine as we
from src import history_manager as hm

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_test_cases_cached():
    return dm.get_test_cases()

@st.cache_data(ttl=300)
def load_refs_cached():
    return dm.get_refs()

@st.cache_data(ttl=300)
def load_prompts_cached():
    return dm.get_prompts()

# ==================== 页面标题 ====================
st.header("🚀 运行中心")
st.markdown("---")

# 加载数据
cases = load_test_cases_cached()
refs_df = load_refs_cached()
all_prompts = load_prompts_cached()

if cases.empty:
    st.warning("⚠️ 暂无测试用例，请前往【测试用例管理】页面添加。")
    st.stop()

# ==================== 模块1: 测试用例选择 ====================
st.info(f"📊 共 **{len(cases)}** 条测试用例，请筛选并勾选要测试的用例")

with st.container(border=True):
    # ========== 筛选器 ==========
    col_car, col_type, col_tag = st.columns([1, 1, 1])
    
    # 获取筛选选项
    car_options = cases['car'].unique().tolist()
    type_options = cases['case_type'].unique().tolist()
    tag_options = cases['problem_tag'].dropna().unique().tolist()
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
        only_goodcase = filter_types == ['goodcase']
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
        filtered_cases = filtered_cases[filtered_cases['car'].isin(filter_cars)]
    
    if filter_types:
        filtered_cases = filtered_cases[filtered_cases['case_type'].isin(filter_types)]
    
    if filter_tags and not only_goodcase:
        filtered_cases = filtered_cases[filtered_cases['problem_tag'].isin(filter_tags)]
    
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
        
        # 获取选中的行索引，然后提取对应的用例
        selected_rows = event.selection.rows
        selected_cases = cases_sorted.iloc[selected_rows] if selected_rows else pd.DataFrame()
    
    st.caption(f"已选择 **{len(selected_cases)}** 条用例")

st.write("")

# ==================== 模块2: 开始测试 ====================
# 初始化测试状态
if 'test_running' not in st.session_state:
    st.session_state.test_running = False

# 没有选择用例时，按钮禁用
no_selection = len(selected_cases) == 0
start_disabled = no_selection or st.session_state.test_running

if no_selection:
    st.warning("⚠️ 请勾选需要测试的用例")

if st.button("▶️ 执行测试", disabled=start_disabled):
    st.session_state.test_running = True
    st.session_state.results = []
    
    # 构建标签到预期节点的映射（用于计算is_precise）
    tags_df = dm.get_problem_tags()
    tag_node_map = {}
    if not tags_df.empty and 'expected_filter_node' in tags_df.columns:
        for _, row in tags_df.iterrows():
            tag_node_map[row['tag_content']] = int(row['expected_filter_node'])
    
    total = len(selected_cases)
    completed = 0
    
    progress_bar = st.progress(0, text="准备中...")
    status_text = st.empty()
    status_text.text("⏳ 正在初始化...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_case = {}
            
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_case = {}
        
        for idx, row in selected_cases.iterrows():
            ref_row = refs_df[refs_df['car'] == row['car']]
            if ref_row.empty:
                status_text.text(f"⚠️ 跳过 Case {row['case_id']}：缺少 {row['car']} 的参考图")
                time.sleep(0.3)
                continue
            
            ref_data = ref_row.iloc[0].to_dict()
            future = executor.submit(we.run_workflow_for_case, row.to_dict(), ref_data, all_prompts)
            future_to_case[future] = row.to_dict()
        
        real_total = len(future_to_case)
        
        if real_total == 0:
            progress_bar.progress(100, text="完成")
            status_text.text("❌ 没有有效任务")
            st.session_state.test_running = False
            st.stop()
        
        for future in as_completed(future_to_case):
            case_info = future_to_case[future]
            try:
                res = future.result()
                
                res['case_id'] = case_info['case_id']
                res['car'] = case_info['car']
                res['case_type'] = case_info['case_type']
                res['problem_tag'] = case_info.get('problem_tag', '')
                res['case_url'] = case_info['case_url']
                
                # 判断is_correct：
                # - badcase: final_pass="no"才算正确
                # - goodcase: final_pass="yes"或"unknown"都算正确
                if case_info['case_type'] == 'badcase':
                    is_correct = (res['final_pass'] == 'no')
                else:
                    is_correct = (res['final_pass'] in ['yes', 'unknown'])
                res['is_correct'] = is_correct
                
                # 计算is_precise（针对所有case）
                # 节点有效率 = 在预期节点被正确处理的case / 所有case
                # - badcase: final_pass="no"且在预期节点被过滤
                # - goodcase: final_pass="yes"且经过节点5（保持严格）
                is_precise = False
                if case_info['case_type'] == 'badcase':
                    problem_tag = case_info.get('problem_tag', '')
                    expected_node = tag_node_map.get(problem_tag, 0)
                    actual_node = res.get('finish_at_step', 0)
                    is_precise = (res['final_pass'] == 'no' and expected_node == actual_node)
                else:
                    is_precise = (res['final_pass'] == 'yes' and res.get('finish_at_step', 0) == 5)
                res['is_precise'] = is_precise
                
                st.session_state.results.append(res)
                
                completed += 1
                progress = completed / real_total
                progress_bar.progress(progress, text=f"进度: {completed}/{real_total}")
                
                # 动态更新状态文本
                icon = '✅' if is_correct else '❌'
                status_text.text(f"{icon} 正在处理 Case {res['case_id']} ({res['car']}) - {completed}/{real_total}")
                
            except Exception as e:
                status_text.text(f"❌ Case {case_info['case_id']} 执行出错: {e}")
                time.sleep(0.5)
    
    status_text.text("✅ 测试执行完毕！")
    
    if st.session_state.results:
        try:
            # tag_node_map已在前面构建，直接使用
            test_id = hm.save_test_history(st.session_state.results, tag_node_map)
            
            correct_count = sum(1 for r in st.session_state.results if r.get('is_correct', False))
            total_count = len(st.session_state.results)
            accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
            
            st.toast("本轮测试完成！", icon="✅")
            st.success(f"""
✅ 测试完成！

- 测试总数: **{total_count}**
- 通过数: **{correct_count}**
- 审图准确率: **{accuracy:.1f}%**
- 测试ID: **{test_id}**

请前往【结果面板】查看详细结果。
            """)
        except Exception as e:
            st.warning(f"⚠️ 测试完成，但保存历史失败: {e}")
    else:
        st.warning("⚠️ 没有测试结果")
    
    st.session_state.test_running = False
