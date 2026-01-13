import streamlit as st
import sys
import os
import pandas as pd
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src import data_manager as dm

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_test_cases_cached():
    return dm.get_test_cases()

@st.cache_data(ttl=300)
def load_problem_tags_cached():
    return dm.get_problem_tags()

@st.cache_data(ttl=300)
def load_refs_cached():
    return dm.get_refs()

# ==================== 页面标题 ====================
st.header("📋 测试用例管理")
st.markdown("---")

# 加载数据
cases = load_test_cases_cached()
tags_df = load_problem_tags_cached()
refs_df = load_refs_cached()

tag_options = tags_df['tag_content'].tolist() if not tags_df.empty else []
available_cars = refs_df['car'].unique().tolist() if not refs_df.empty else []

if not available_cars:
    st.warning("⚠️ 暂无已配置参考图的车系，请先前往【参考图库管理】添加车系参考图！")
    st.stop()

# ==================== Dialog: 新增用例 ====================
@st.dialog("➕ 新增测试用例", width="medium")
def show_add_case_dialog():
    # 获取默认值（继承最后一条数据）
    default_car = available_cars[0]
    default_type = "badcase"
    default_tag = tag_options[0] if tag_options else ""
    
    if not cases.empty:
        last_row = cases.iloc[-1]
        if last_row['car'] in available_cars:
            default_car = last_row['car']
        if last_row['case_type'] in ["badcase", "goodcase"]:
            default_type = last_row['case_type']
        if last_row['problem_tag'] in tag_options:
            default_tag = last_row['problem_tag']
    
    col1, col2 = st.columns([1, 1])
    with col1:
        new_car = st.selectbox(
            "车系名称",
            available_cars,
            index=available_cars.index(default_car) if default_car in available_cars else 0,
            key="add_car"
        )
    with col2:
        new_type = st.selectbox(
            "用例类型",
            ["badcase", "goodcase"],
            index=0 if default_type == "badcase" else 1,
            key="add_type"
        )
    
    # 问题标签（只能从已有标签选择）
    new_tag = st.selectbox(
        "问题标签",
        tag_options if tag_options else [""],
        index=tag_options.index(default_tag) if default_tag in tag_options else 0,
        key="add_tag",
        disabled=(new_type == "goodcase"),
        help="仅badcase需要，如需新增标签请前往【配置管理】"
    )
    
    new_url = st.text_input("图片URL", placeholder="https://...", key="add_url")
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认添加", type="primary"):
            if not new_url:
                st.error("❌ 图片URL不能为空")
            else:
                current_cases = dm.get_test_cases()
                new_id = str(len(current_cases) + 1)
                new_case = {
                    "case_id": new_id,
                    "car": new_car,
                    "case_type": new_type,
                    "problem_tag": new_tag if new_type == "badcase" else "",
                    "case_url": new_url
                }
                dm.save_test_case(new_case)
                load_test_cases_cached.clear()
                st.toast("用例添加成功！", icon="✅")
                time.sleep(0.5)
                st.rerun()
    
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 编辑用例 ====================
@st.dialog("✏️ 编辑测试用例", width="medium")
def show_edit_case_dialog(case_data):
    col1, col2 = st.columns([1, 1])
    with col1:
        edit_car = st.selectbox(
            "车系名称",
            available_cars,
            index=available_cars.index(case_data['car']) if case_data['car'] in available_cars else 0,
            key="edit_car"
        )
    with col2:
        edit_type = st.selectbox(
            "用例类型",
            ["badcase", "goodcase"],
            index=0 if case_data['case_type'] == "badcase" else 1,
            key="edit_type"
        )
    
    current_tag = case_data.get('problem_tag', '')
    tag_index = tag_options.index(current_tag) if current_tag in tag_options else 0
    edit_tag = st.selectbox(
        "问题标签",
        tag_options if tag_options else [""],
        index=tag_index,
        key="edit_tag",
        disabled=(edit_type == "goodcase"),
        help="仅badcase需要，如需新增标签请前往【配置管理】"
    )
    
    edit_url = st.text_input("图片URL", value=case_data['case_url'], key="edit_url")
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认修改", type="primary"):
            if not edit_url:
                st.error("❌ 图片URL不能为空")
            else:
                all_cases = dm.get_test_cases()
                idx = all_cases[all_cases['case_id'] == case_data['case_id']].index
                if len(idx) > 0:
                    all_cases.loc[idx[0], 'car'] = edit_car
                    all_cases.loc[idx[0], 'case_type'] = edit_type
                    all_cases.loc[idx[0], 'problem_tag'] = edit_tag if edit_type == "badcase" else ""
                    all_cases.loc[idx[0], 'case_url'] = edit_url
                    dm.save_csv("test_cases.csv", all_cases)
                    load_test_cases_cached.clear()
                    st.toast("用例修改成功！", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
    
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 图片预览 ====================
@st.dialog("🖼️ 图片预览", width="medium")
def show_preview_dialog(case_data):
    st.markdown(f"""
**ID:** {case_data['case_id']}  
**车系:** {case_data['car']}  
**类型:** {case_data['case_type']}  
**标签:** {case_data.get('problem_tag') or '无'}
    """)
    
    url = case_data['case_url']
    if url and str(url).startswith('http'):
        st.image(url, caption="测试用例图片")
    else:
        st.warning("无效的图片URL")
    
    if st.button("关闭", type="primary"):
        st.rerun()

# ==================== 模块: 用例管理 ====================
with st.container(border=True):
    # ========== 筛选器 ==========
    col_car, col_type, col_tag = st.columns([1, 1, 1])
    
    car_filter_options = cases['car'].unique().tolist() if not cases.empty else []
    type_filter_options = cases['case_type'].unique().tolist() if not cases.empty else []
    tag_filter_options = cases['problem_tag'].dropna().unique().tolist() if not cases.empty else []
    tag_filter_options = [t for t in tag_filter_options if t]
    
    with col_car:
        filter_cars = st.multiselect(
            "车系",
            options=car_filter_options,
            default=[],
            placeholder="全部车系",
            key="case_filter_car"
        )
    
    with col_type:
        filter_types = st.multiselect(
            "类型",
            options=type_filter_options,
            default=[],
            placeholder="全部类型",
            key="case_filter_type"
        )
    
    with col_tag:
        only_goodcase = filter_types == ['goodcase']
        filter_tags = st.multiselect(
            "问题标签",
            options=tag_filter_options,
            default=[],
            placeholder="全部标签" if not only_goodcase else "goodcase无标签",
            disabled=only_goodcase,
            key="case_filter_tag"
        )
    
    # ========== 应用筛选 ==========
    filtered_cases = cases.copy() if not cases.empty else pd.DataFrame()
    
    if not filtered_cases.empty:
        if filter_cars:
            filtered_cases = filtered_cases[filtered_cases['car'].isin(filter_cars)]
        if filter_types:
            filtered_cases = filtered_cases[filtered_cases['case_type'].isin(filter_types)]
        if filter_tags and not only_goodcase:
            filtered_cases = filtered_cases[filtered_cases['problem_tag'].isin(filter_tags)]
    
    # 降序展示
    cases_sorted = filtered_cases.iloc[::-1].reset_index(drop=True) if not filtered_cases.empty else pd.DataFrame()
    
    st.caption(f"筛选后共 **{len(cases_sorted)}** 条用例")
    
    # ========== 操作按钮 ==========
    btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([1, 1, 1, 1, 2])
    
    with btn_col1:
        if st.button("➕ 新增", key="btn_add_case"):
            show_add_case_dialog()
    
    # 获取选中状态（用于控制按钮）
    selected_rows = []
    selected_cases_data = pd.DataFrame()
    
    # ========== 表格展示 ==========
    if cases_sorted.empty:
        st.info("暂无符合条件的用例")
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
            height=400,
            on_select="rerun",
            selection_mode="multi-row",
            key="case_table_selector"
        )
        
        selected_rows = event.selection.rows
        selected_cases_data = cases_sorted.iloc[selected_rows] if selected_rows else pd.DataFrame()
    
    # 预览、编辑、删除按钮（顺序：新增、预览、编辑、删除）
    with btn_col2:
        preview_disabled = len(selected_rows) != 1
        if st.button("🖼️ 预览", disabled=preview_disabled, key="btn_preview_case"):
            case_to_preview = selected_cases_data.iloc[0].to_dict()
            show_preview_dialog(case_to_preview)
    
    with btn_col3:
        edit_disabled = len(selected_rows) != 1
        if st.button("✏️ 编辑", disabled=edit_disabled, key="btn_edit_case"):
            case_to_edit = selected_cases_data.iloc[0].to_dict()
            show_edit_case_dialog(case_to_edit)
    
    with btn_col4:
        delete_disabled = len(selected_rows) == 0
        if st.button("🗑️ 删除", disabled=delete_disabled, key="btn_delete_case"):
            st.session_state.show_delete_confirm = True
    
    # 删除确认
    if st.session_state.get('show_delete_confirm', False) and len(selected_rows) > 0:
        st.warning(f"⚠️ 确定要删除选中的 **{len(selected_rows)}** 条用例吗？")
        confirm_col1, confirm_col2, _ = st.columns([1, 1, 4])
        with confirm_col1:
            if st.button("✅ 确认删除", type="primary"):
                ids_to_delete = selected_cases_data['case_id'].tolist()
                all_cases = dm.get_test_cases()
                all_cases = all_cases[~all_cases['case_id'].isin(ids_to_delete)]
                # 重新编号
                all_cases = all_cases.reset_index(drop=True)
                all_cases['case_id'] = (all_cases.index + 1).astype(str)
                dm.save_csv("test_cases.csv", all_cases)
                load_test_cases_cached.clear()
                st.session_state.show_delete_confirm = False
                st.toast(f"已删除 {len(ids_to_delete)} 条用例！", icon="✅")
                time.sleep(0.5)
                st.rerun()
        with confirm_col2:
            if st.button("❌ 取消"):
                st.session_state.show_delete_confirm = False
                st.rerun()
    
    # 选中状态提示
    if selected_rows:
        st.caption(f"已选择 **{len(selected_rows)}** 条用例")
