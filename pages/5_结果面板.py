import streamlit as st
import pandas as pd
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src import history_manager as hm

# ==================== 页面配置 ====================
st.set_page_config(page_title="结果面板", page_icon="📊", layout="wide")
st.title("📊 结果面板")
st.markdown("---")

# Tab切换
tab1, tab2 = st.tabs(["📋 当前测试结果", "📚 历史测试记录"])

# ==================== Tab1: 当前测试结果 ====================
with tab1:
    with st.container(border=True):
        if 'results' not in st.session_state or not st.session_state.results:
            st.info("暂无数据，请先在【运行中心】执行测试。")
        else:
            results_df = pd.DataFrame(st.session_state.results)
            
            # 核心指标
            total_runs = len(results_df)
            correct_runs = len(results_df[results_df['is_correct'] == True])
            accuracy = (correct_runs / total_runs * 100) if total_runs > 0 else 0
            
            st.markdown("#### 📈 核心指标")
            col1, col2, col3 = st.columns(3)
            col1.metric("测试总数", total_runs)
            col2.metric("通过数", correct_runs)
            col3.metric("准确率", f"{accuracy:.1f}%")
            
            st.divider()
            
            # 详细列表
            st.markdown("#### 📝 详细列表")
            
            # 筛选
            filter_opt = st.radio(
                "筛选",
                ["全部", "仅错误", "仅正确"],
                horizontal=True,
                key="current_filter"
            )
            
            display_df = results_df
            if filter_opt == "仅错误":
                display_df = results_df[results_df['is_correct'] == False]
            elif filter_opt == "仅正确":
                display_df = results_df[results_df['is_correct'] == True]
            
            if display_df.empty:
                st.info("无匹配结果")
            else:
                for i, row in display_df.iterrows():
                    status_icon = "✅" if row['is_correct'] else "❌"
                    expected = "no" if row['case_type'] == 'badcase' else "yes"
                    
                    with st.expander(
                        f"{status_icon} [{row['case_id']}] {row['car']} | 预期: {expected} | 实际: {row['final_pass']}",
                        expanded=False
                    ):
                        # 在卡片内显示完整JSON
                        result_json = {
                            "case_id": row['case_id'],
                            "car": row['car'],
                            "case_type": row['case_type'],
                            "problem_tag": row.get('problem_tag', ''),
                            "case_url": row['case_url'],
                            "expected_pass": expected,
                            "final_pass": row['final_pass'],
                            "is_correct": row['is_correct'],
                            "finish_at_step": row['finish_at_step'],
                            "reason": row.get('reason', ''),
                            "parse_output": row.get('parse_output', {}),
                            "prompt_versions": row.get('prompt_versions', {}),
                            "model_config": row.get('model_config', {})
                        }
                        st.json(result_json, expanded=True)

# ==================== Tab2: 历史测试记录 ====================
with tab2:
    history_list = hm.list_test_history()
    
    with st.container(border=True):
        if not history_list:
            st.info("暂无历史记录，请先在【运行中心】执行测试。")
        else:
            st.caption(f"共 **{len(history_list)}** 条历史记录")
            
            # 显示历史列表
            for hist in history_list:
                with st.expander(
                    f"🕒 {hist['test_id']} | 准确率: {hist['acc_rate']*100:.1f}% | 测试数: {hist['cases_total']}",
                    expanded=False
                ):
                    # 基本信息
                    col_info, col_actions = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"""
**测试时间:** {hist['test_time']}  
**测试总数:** {hist['cases_total']}  
**通过数:** {hist['acc_total']}  
**准确率:** {hist['acc_rate']*100:.1f}%
                        """)
                    
                    with col_actions:
                        if st.button("🗑️ 删除", key=f"del_{hist['test_id']}", type="secondary"):
                            if hm.delete_test_history(hist['test_id']):
                                st.toast(f"已删除 {hist['test_id']}", icon="✅")
                                time.sleep(0.8)
                                st.rerun()
                            else:
                                st.error("删除失败")
                    
                    st.divider()
                    
                    # 详情直接展示在卡片内
                    st.markdown("**📋 详细数据**")
                    history_data = hm.load_test_history(hist['test_id'])
                    if history_data:
                        st.json(history_data, expanded=False)
                    else:
                        st.warning("无法加载详情数据")
