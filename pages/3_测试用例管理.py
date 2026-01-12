import streamlit as st
import sys
import os
import pandas as pd
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
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

# ==================== 页面配置 ====================
st.set_page_config(page_title="测试用例管理", page_icon="📋", layout="wide")
st.title("📋 测试用例管理")
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

# ==================== 模块1: 标签管理 ====================
st.markdown("### 1. 标签管理")
with st.container(border=True):
    tab_tag_add, tab_tag_list = st.tabs(["➕ 新增标签", "📋 标签列表"])
    
    # Tab1: 新增标签
    with tab_tag_add:
        if 'tag_form_key' not in st.session_state:
            st.session_state.tag_form_key = 0
        
        with st.form(key=f"add_tag_form_{st.session_state.tag_form_key}"):
            new_tag_content = st.text_input("标签名称", placeholder="例如: 裁切、车牌文字、无人驾驶...")
            submitted = st.form_submit_button("➕ 添加标签")
            
            if submitted:
                if not new_tag_content:
                    st.error("❌ 标签名称不能为空")
                else:
                    dm.add_problem_tag(new_tag_content)
                    load_problem_tags_cached.clear()
                    st.toast("标签添加成功！", icon="✅")
                    st.session_state.tag_form_key += 1
                    time.sleep(0.8)
                    st.rerun()
    
    # Tab2: 标签列表
    with tab_tag_list:
        if tags_df.empty:
            st.info("暂无标签，请先添加。")
        else:
            st.caption(f"共 **{len(tags_df)}** 个标签")
            
            edited_tags = st.data_editor(
                tags_df,
                column_config={
                    "tag_id": st.column_config.NumberColumn("ID", disabled=True, format="%d", width="small"),
                    "tag_content": st.column_config.TextColumn("标签名称", required=True, width="large")
                },
                hide_index=True,
                num_rows="dynamic",
                width='stretch',
                key="tags_editor"
            )
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("💾 保存修改", key="save_tags"):
                    dm.save_csv("problem_tags.csv", edited_tags)
                    load_problem_tags_cached.clear()
                    st.toast("标签已保存！", icon="✅")
                    time.sleep(0.8)
                    st.rerun()

st.write("")

# ==================== 模块2: 用例管理 ====================
st.markdown("### 2. 用例管理")
with st.container(border=True):
    tab_case_add, tab_case_list = st.tabs(["➕ 新增用例", "📋 用例列表"])
    
    # Tab1: 新增用例
    with tab_case_add:
        if 'case_form_key' not in st.session_state:
            st.session_state.case_form_key = 0
        
        # 获取默认值
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
        
        with st.form(key=f"add_case_form_{st.session_state.case_form_key}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                acc_car = st.selectbox(
                    "车系名称",
                    available_cars,
                    index=available_cars.index(default_car) if default_car in available_cars else 0
                )
            with col2:
                acc_type = st.selectbox(
                    "用例类型",
                    ["badcase", "goodcase"],
                    index=0 if default_type == "badcase" else 1
                )
            with col3:
                acc_tag = st.selectbox(
                    "问题标签",
                    tag_options if tag_options else [""],
                    index=tag_options.index(default_tag) if default_tag in tag_options else 0,
                    help="仅badcase需要"
                )
            
            acc_url = st.text_input("图片URL", placeholder="https://...")
            
            submitted = st.form_submit_button("➕ 添加用例")
            
            if submitted:
                if not acc_url:
                    st.error("❌ 图片URL不能为空")
                else:
                    current_cases = dm.get_test_cases()
                    new_id = str(len(current_cases) + 1)
                    
                    new_case = {
                        "case_id": new_id,
                        "car": acc_car,
                        "case_type": acc_type,
                        "problem_tag": acc_tag if acc_type == "badcase" else "",
                        "case_url": acc_url
                    }
                    dm.save_test_case(new_case)
                    load_test_cases_cached.clear()
                    st.toast("用例添加成功！", icon="✅")
                    st.session_state.case_form_key += 1
                    time.sleep(0.8)
                    st.rerun()
    
    # Tab2: 用例列表
    with tab_case_list:
        if cases.empty:
            st.info("暂无用例，请先添加。")
        else:
            st.caption(f"共 **{len(cases)}** 条用例")
            
            # 降序排列
            cases_sorted = cases.iloc[::-1].reset_index(drop=True)
            
            # 重新加载标签选项
            current_tags = load_problem_tags_cached()
            current_tag_options = [""] + current_tags['tag_content'].tolist() if not current_tags.empty else [""]
            
            edited_cases = st.data_editor(
                cases_sorted,
                column_config={
                    "case_id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "car": st.column_config.SelectboxColumn("车系", options=available_cars, width="medium"),
                    "case_type": st.column_config.SelectboxColumn("类型", options=["badcase", "goodcase"], width="small"),
                    "problem_tag": st.column_config.SelectboxColumn("问题标签", options=current_tag_options, width="medium"),
                    "case_url": st.column_config.LinkColumn("图片", display_text="🔗 Link", width="small"),
                },
                hide_index=True,
                num_rows="dynamic",
                height=400,
                width='stretch',
                key="case_editor"
            )
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("💾 保存修改", key="save_cases"):
                    # 恢复原始顺序
                    save_df = edited_cases.iloc[::-1].reset_index(drop=True)
                    save_df['case_id'] = (save_df.index + 1).astype(str)
                    dm.save_csv("test_cases.csv", save_df)
                    load_test_cases_cached.clear()
                    st.toast("数据已保存！", icon="✅")
                    time.sleep(0.8)
                    st.rerun()

st.write("")

# ==================== 模块3: 图片预览 ====================
st.markdown("### 3. 图片预览")
with st.container(border=True):
    if cases.empty:
        st.info("暂无用例可预览。")
    else:
        case_ids = cases['case_id'].tolist()
        
        selected_case_id = st.selectbox(
            "选择用例",
            case_ids[::-1],
            index=0,
            key="preview_case_select"
        )
        
        if selected_case_id:
            row = cases[cases['case_id'] == selected_case_id].iloc[0]
            
            col_info, col_img = st.columns([1, 1])
            
            with col_info:
                st.info(f"""
**用例ID:** {row['case_id']}

**车系:** {row['car']}

**类型:** {row['case_type']}

**问题标签:** {row['problem_tag'] if row['problem_tag'] else '无'}
                """)
            
            with col_img:
                url = row['case_url']
                if url and str(url).startswith('http'):
                    st.image(url, width=100)
                else:
                    st.warning("⚠️ 无效的图片URL")
