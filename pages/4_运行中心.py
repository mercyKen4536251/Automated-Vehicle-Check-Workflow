import streamlit as st
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
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

# ==================== 页面配置 ====================
st.set_page_config(page_title="运行中心", page_icon="🚀", layout="wide")
st.title("🚀 运行中心")
st.markdown("---")

# 加载数据
cases = load_test_cases_cached()
refs_df = load_refs_cached()
all_prompts = load_prompts_cached()

if cases.empty:
    st.warning("⚠️ 暂无测试用例，请前往【测试用例管理】页面添加。")
    st.stop()

# ==================== 模块1: 测试用例选择 ====================
st.info(f"📊 共 **{len(cases)}** 条测试用例")

with st.container(border=True):   
    # 降序展示
    cases_sorted = cases.iloc[::-1].reset_index(drop=True)
    
    # 使用 data_editor，添加 num_rows="dynamic" 会自动显示左侧选择框
    cases_display = st.data_editor(
        cases_sorted,
        column_config={
            "case_id": st.column_config.TextColumn("ID", disabled=True, width="small"),
            "car": st.column_config.TextColumn("车系", disabled=True, width="medium"),
            "case_type": st.column_config.TextColumn("类型", disabled=True, width="small"),
            "problem_tag": st.column_config.TextColumn("问题标签", disabled=True, width="small"),
            "case_url": st.column_config.LinkColumn("图片", display_text="🔗 Link", width="small"),
        },
        hide_index=True,
        num_rows="dynamic",
        height=350,
        width='stretch',
        key="run_case_selector"
    )
    
    # 获取选中的用例（通过对比原始数据和编辑后的数据）
    # num_rows="dynamic" 允许用户删除行，删除的行就是未选中的
    selected_case_ids = cases_display['case_id'].tolist()
    selected_cases = cases_sorted[cases_sorted['case_id'].isin(selected_case_ids)]
    
    st.caption(f"已选择 **{len(selected_cases)}** 条用例（删除行 = 不选择）")

st.write("")

# ==================== 模块2: 开始测试 ====================
# 初始化测试状态
if 'test_running' not in st.session_state:
    st.session_state.test_running = False

start_disabled = len(selected_cases) == 0 or st.session_state.test_running

if st.button("▶️ 立即开始测试", disabled=start_disabled,):
    if len(selected_cases) == 0:
        st.toast("请先选择测试用例", icon="⚠️")
    else:
        st.session_state.test_running = True
        st.session_state.results = []
        
        total = len(selected_cases)
        completed = 0
        
        progress_bar = st.progress(0, text="准备中...")
        
        with st.status("🚀 测试执行中...", expanded=True) as status:
            status.write("正在初始化...")
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_case = {}
                
                for idx, row in selected_cases.iterrows():
                    ref_row = refs_df[refs_df['car'] == row['car']]
                    if ref_row.empty:
                        status.write(f"⚠️ 跳过 Case {row['case_id']}：缺少 {row['car']} 的参考图")
                        continue
                    
                    ref_data = ref_row.iloc[0].to_dict()
                    future = executor.submit(we.run_workflow_for_case, row.to_dict(), ref_data, all_prompts)
                    future_to_case[future] = row.to_dict()
                
                real_total = len(future_to_case)
                
                if real_total == 0:
                    progress_bar.progress(100, text="完成")
                    status.update(label="❌ 没有有效任务", state="error")
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
                        
                        expected_pass = "no" if case_info['case_type'] == 'badcase' else "yes"
                        is_correct = (res['final_pass'] == expected_pass)
                        res['is_correct'] = is_correct
                        
                        st.session_state.results.append(res)
                        
                        completed += 1
                        progress = completed / real_total
                        progress_bar.progress(progress, text=f"进度: {completed}/{real_total}")
                        
                        icon = '✅' if is_correct else '❌'
                        status.write(f"{icon} Case {res['case_id']} | {res['car']} | 预期: {expected_pass} | 实际: {res['final_pass']}")
                        
                    except Exception as e:
                        status.write(f"❌ Case {case_info['case_id']} 执行出错: {e}")
            
            status.update(label="✅ 测试执行完毕!", state="complete")
        
        if st.session_state.results:
            try:
                test_id = hm.save_test_history(st.session_state.results)
                
                correct_count = sum(1 for r in st.session_state.results if r.get('is_correct', False))
                total_count = len(st.session_state.results)
                accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
                
                st.toast("本轮测试完成！", icon="✅")
                st.success(f"""
✅ 测试完成！

- 测试总数: **{total_count}**
- 通过数: **{correct_count}**
- 准确率: **{accuracy:.1f}%**
- 测试ID: **{test_id}**

请前往【结果面板】查看详细结果。
                """)
            except Exception as e:
                st.warning(f"⚠️ 测试完成，但保存历史失败: {e}")
        else:
            st.warning("⚠️ 没有测试结果")
        
        st.session_state.test_running = False
