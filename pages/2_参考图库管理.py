import streamlit as st
import sys
import os
import pandas as pd
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src import data_manager as dm

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_refs_cached():
    return dm.get_refs()

# ==================== 页面配置 ====================
st.set_page_config(page_title="参考图库管理", page_icon="🖼️", layout="wide")
st.title("🖼️ 参考图库管理")
st.markdown("---")

# 加载数据
refs = load_refs_cached()

# ==================== 模块1: 参考图管理 ====================
st.markdown("### 1. 参考图管理")
with st.container(border=True):
    tab_add, tab_list = st.tabs(["➕ 新增车系", "📋 车系列表"])
    
    # ==================== Tab1: 新增车系 ====================
    with tab_add:
        if 'ref_form_key' not in st.session_state:
            st.session_state.ref_form_key = 0
        
        with st.form(key=f"add_ref_form_{st.session_state.ref_form_key}"):
            c_car = st.text_input("车系名称", placeholder="例如: 问界M9")
            c_url_1 = st.text_input("参考图 1", placeholder="https://...", key="ref_url_1")
            c_url_2 = st.text_input("参考图 2", placeholder="https://...", key="ref_url_2")
            c_url_3 = st.text_input("参考图 3", placeholder="https://...", key="ref_url_3")
            c_url_4 = st.text_input("参考图 4", placeholder="https://...", key="ref_url_4")
            c_url_5 = st.text_input("参考图 5", placeholder="https://...", key="ref_url_5")
            
            submitted = st.form_submit_button("➕ 确认添加")
            
            if submitted:
                if not c_car:
                    st.error("❌ 车系名称不能为空")
                else:
                    current_refs = dm.get_refs()
                    new_id = str(len(current_refs) + 1)
                    
                    row = {
                        "ref_id": new_id,
                        "car": c_car,
                        "ref_url_1": c_url_1,
                        "ref_url_2": c_url_2,
                        "ref_url_3": c_url_3,
                        "ref_url_4": c_url_4,
                        "ref_url_5": c_url_5
                    }
                    current_refs = pd.concat([current_refs, pd.DataFrame([row])], ignore_index=True)
                    dm.save_csv("ref.csv", current_refs)
                    load_refs_cached.clear()
                    st.toast(f"车系 {c_car} 已添加！", icon="✅")
                    st.session_state.ref_form_key += 1
                    time.sleep(0.8)
                    st.rerun()
    
    # ==================== Tab2: 车系列表 ====================
    with tab_list:
        if refs.empty:
            st.info("暂无数据，请先在【新增车系】页面添加。")
        else:
            st.caption(f"共 **{len(refs)}** 个车系")
            
            edited_df = st.data_editor(
                refs,
                column_config={
                    "ref_id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                    "car": st.column_config.TextColumn("车系名称", required=True, width="medium"),
                    "ref_url_1": st.column_config.LinkColumn("参考图1", display_text="🔗 Link", width="small"),
                    "ref_url_2": st.column_config.LinkColumn("参考图2", display_text="🔗 Link", width="small"),
                    "ref_url_3": st.column_config.LinkColumn("参考图3", display_text="🔗 Link", width="small"),
                    "ref_url_4": st.column_config.LinkColumn("参考图4", display_text="🔗 Link", width="small"),
                    "ref_url_5": st.column_config.LinkColumn("参考图5", display_text="🔗 Link", width="small"),
                },
                hide_index=True,
                num_rows="dynamic",
                height=400,
                width='stretch',
                key="ref_editor"
            )
            
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("💾 保存修改", key="save_ref"):
                    save_df = edited_df.reset_index(drop=True)
                    save_df['ref_id'] = (save_df.index + 1).astype(str)
                    dm.save_csv("ref.csv", save_df)
                    load_refs_cached.clear()
                    st.toast("数据已保存！", icon="✅")
                    time.sleep(0.8)
                    st.rerun()

st.write("")

# ==================== 模块2: 图片预览 ====================
st.markdown("### 2. 图片预览")
with st.container(border=True):
    if refs.empty:
        st.info("暂无车系可预览，请先添加车系。")
    else:
        car_list = refs['car'].unique().tolist()
        
        if 'preview_car' not in st.session_state:
            st.session_state.preview_car = car_list[0] if car_list else None
        
        selected_car = st.selectbox(
            "选择车系",
            car_list,
            index=car_list.index(st.session_state.preview_car) if st.session_state.preview_car in car_list else 0,
            key="preview_car_select"
        )
        st.session_state.preview_car = selected_car
        
        if selected_car:
            row = refs[refs['car'] == selected_car].iloc[0]
            
            cols = st.columns(5)
            for i in range(1, 6):
                url = row.get(f"ref_url_{i}")
                with cols[i-1]:
                    if pd.notna(url) and str(url).strip().startswith("http"):
                        st.image(str(url), caption=f"参考图 {i}")
                    else:
                        st.caption(f"参考图 {i}")
                        st.markdown("*（空）*")
