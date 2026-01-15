import streamlit as st
import pandas as pd
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from src import history_manager as hm

# ==================== 页面标题 ====================
st.header("📊 结果面板")
st.markdown("---")

# ==================== 初始化session_state ====================
if "selected_test_id" not in st.session_state:
    st.session_state.selected_test_id = None

# 加载历史记录列表
history_list = hm.list_test_history()

# ==================== 主容器 ====================
with st.container(border=True):
    tab1, tab2 = st.tabs(["📋 测试记录", "🔍 详细结果"])
    
    # ==================== Tab1: 测试记录 ====================
    with tab1:
        if not history_list:
            st.info("暂无测试记录，请先执行测试。")
        else:
            st.caption(f"共 **{len(history_list)}** 条测试记录")
            
            for i, hist in enumerate(history_list):
                full_data = hm.load_test_history(hist["test_id"])
                node_eff = full_data.get("node_efficiency", 0) * 100 if full_data else 0
                
                is_expanded = (i == 0)
                
                with st.expander(
                    f"🕒编号：_{hist['test_id']}_ | 审图准确率: _{hist['acc_rate']*100:.1f}%_ | 节点有效率: _{node_eff:.1f}%_ | 测试总数: _{hist['cases_total']}_",
                    expanded=is_expanded
                ):
                    col_info, col_actions = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"- **测试时间:** _{hist['test_time']}_")
                        st.markdown(f"- **测试总数:** _{hist['cases_total']}_")
                        st.markdown(f"- **通过数:** _{hist['acc_total']}_")
                        st.markdown(f"- **审图准确率:** _{hist['acc_rate']*100:.1f}%_")
                        st.markdown(f"- **节点有效率:** _{node_eff:.1f}%_")
                    
                    with col_actions:
                        if st.button("📄 查看详情", key=f"view_{hist['test_id']}", type="primary"):
                            st.session_state.selected_test_id = hist["test_id"]
                            st.rerun()
                        
                        if st.button("🗑️ 删除", key=f"del_{hist['test_id']}", type="secondary"):
                            if hm.delete_test_history(hist["test_id"]):
                                if st.session_state.selected_test_id == hist["test_id"]:
                                    st.session_state.selected_test_id = None
                                st.toast(f"已删除 {hist['test_id']}", icon="✅")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("删除失败")

    # ==================== Tab2: 详细结果 ====================
    with tab2:
        if st.session_state.selected_test_id is None:
            st.info("👈 请在【测试记录】中选择要查看的测试结果")
        else:
            test_data = hm.load_test_history(st.session_state.selected_test_id)
            
            if not test_data:
                st.error("无法加载测试数据")
                st.session_state.selected_test_id = None
            else:
                results = test_data.get("results", [])
                results_df = pd.DataFrame(results)
                
                if results_df.empty:
                    st.warning("该测试记录无详细数据")
                else:
                    # ========== 测试记录标题 ==========
                    st.markdown(f"#### 📈 测试记录: {st.session_state.selected_test_id}")
                    
                    # ========== 配置信息 ==========
                    model_config = test_data.get("model_config", {})
                    prompt_versions = test_data.get("prompt_versions", {})
                    
                    model_id = model_config.get("model_id", "未知")
                    thinking_mode = model_config.get("thinking_mode", "未知")
                    versions_str = " | ".join([f"{k}: {v}" for k, v in prompt_versions.items()]) if prompt_versions else "未知"
                    
                    st.info(f"**模型:** {model_id}  \n\n**思考模式:** {thinking_mode}  \n\n**提示词版本:** {versions_str}")
                    st.write("")

                    # ========== 筛选器 ==========
                    st.markdown("#### 📝 详细列表")
                    
                    car_options = results_df["car"].unique().tolist()
                    type_options = results_df["case_type"].unique().tolist()
                    tag_options = results_df["problem_tag"].dropna().unique().tolist()
                    tag_options = [t for t in tag_options if t]
                    
                    col_result, col_car, col_type, col_tag = st.columns([1, 1, 1, 1])
                    
                    with col_result:
                        filter_result = st.selectbox(
                            "结果筛选",
                            ["全部", "仅正确", "仅错误", "节点不精准"],
                            key="filter_result"
                        )
                    
                    with col_car:
                        filter_cars = st.multiselect(
                            "车系",
                            options=car_options,
                            default=[],
                            placeholder="全部车系",
                            key="detail_filter_car"
                        )
                    
                    with col_type:
                        filter_types = st.multiselect(
                            "类型",
                            options=type_options,
                            default=[],
                            placeholder="全部类型",
                            key="detail_filter_type"
                        )
                    
                    with col_tag:
                        only_goodcase = filter_types == ["goodcase"]
                        filter_tags = st.multiselect(
                            "问题标签",
                            options=tag_options,
                            default=[],
                            placeholder="全部标签" if not only_goodcase else "goodcase无标签",
                            disabled=only_goodcase,
                            key="detail_filter_tag"
                        )
                    
                    # ========== 应用筛选 ==========
                    display_df = results_df.copy()
                    
                    # 重新计算is_correct（使用新逻辑，不依赖历史数据）
                    def recalculate_is_correct(row):
                        if row["case_type"] == "badcase":
                            return row["final_pass"] == "no"
                        else:
                            return row["final_pass"] in ["yes", "unknown"]
                    
                    display_df["is_correct"] = display_df.apply(recalculate_is_correct, axis=1)
                    
                    if filter_result == "仅正确":
                        display_df = display_df[display_df["is_correct"] == True]
                    elif filter_result == "仅错误":
                        display_df = display_df[display_df["is_correct"] == False]
                    elif filter_result == "节点不精准":
                        if "is_precise" in display_df.columns:
                            display_df = display_df[display_df["is_precise"] == False]
                        else:
                            display_df = pd.DataFrame()
                    
                    if filter_cars:
                        display_df = display_df[display_df["car"].isin(filter_cars)]
                    
                    if filter_types:
                        display_df = display_df[display_df["case_type"].isin(filter_types)]
                    
                    if filter_tags and not only_goodcase:
                        display_df = display_df[display_df["problem_tag"].isin(filter_tags)]
                    
                    # ========== 核心指标（基于筛选后的数据实时计算）==========
                    total_runs = len(display_df)
                    correct_runs = len(display_df[display_df["is_correct"] == True]) if total_runs > 0 else 0
                    accuracy = (correct_runs / total_runs * 100) if total_runs > 0 else 0
                    
                    if "is_precise" in display_df.columns and total_runs > 0:
                        precise_count = len(display_df[display_df["is_precise"] == True])
                    else:
                        precise_count = 0
                    node_efficiency = (precise_count / total_runs * 100) if total_runs > 0 else 0
                    
                    st.markdown("---")

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("测试总数", total_runs)
                    col2.metric("通过数", correct_runs)
                    col3.metric("审图准确率", f"{accuracy:.1f}%")
                    col4.metric("节点有效率", f"{node_efficiency:.1f}%", help="在预期节点被正确处理的case占比")

                    st.markdown("---")
                    
                    st.caption(f"筛选后共 **{len(display_df)}** 条结果")

                    # ========== 结果列表 ==========
                    if display_df.empty:
                        st.info("无匹配结果")
                    else:
                        for idx, row in display_df.iterrows():
                            status_icon = "✅" if row["is_correct"] else "❌"
                            expected = row.get("expected_pass", "no" if row["case_type"] == "badcase" else "yes")
                            
                            node_info = f"节点{row['finish_at_step']}"
                            if "is_precise" in row and not row.get("is_precise", True):
                                node_info += " ⚠️"
                            
                            with st.expander(
                                f"{status_icon} [_{row['case_id']}_] | {row['car']} | {node_info} | 正确结果: _{expected}_ | 实际结果: _{row['final_pass']}_",
                                expanded=False
                            ):
                                col_info, col_img, col_json = st.columns([1, 1, 2])
                                
                                with col_info:
                                    st.markdown("**基础信息**")
                                    st.markdown(f"- **编号:** _{row['case_id']}_")
                                    st.markdown(f"- **车系:** {row['car']}")
                                    st.markdown(f"- **类型:** _{row['case_type']}_")
                                    st.markdown(f"- **标签:** {row.get('problem_tag') or '无'}")
                                
                                with col_img:
                                    st.markdown("**图片预览**")
                                    case_url = row.get("case_url", "")
                                    if case_url and str(case_url).startswith("http"):
                                        st.image(case_url, width=160)
                                    else:
                                        st.warning("无效图片URL")
                                
                                with col_json:
                                    st.markdown("**模型输出**")
                                    output_data = {
                                        "parse_output": row.get("parse_output", {}),
                                        "expected_filter_node": row.get("expected_filter_node", 0),
                                        "finish_at_step": row.get("finish_at_step", 0)
                                    }
                                    st.json(output_data, expanded=True)
