import streamlit as st
import sys
import os
import pandas as pd
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src import data_manager as dm

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_refs_cached():
    return dm.get_refs()

# ==================== 页面标题 ====================
st.header("🖼️ 参考图库管理")
st.markdown("---")

# 加载数据
refs = load_refs_cached()

# ==================== Dialog: 新增车系 ====================
@st.dialog("➕ 新增车系", width="medium")
def show_add_ref_dialog():
    new_car = st.text_input("车系名称", placeholder="例如: 问界M9", key="add_ref_car")
    new_url_1 = st.text_input("参考图 1", placeholder="https://...", key="add_ref_url_1")
    new_url_2 = st.text_input("参考图 2", placeholder="https://...", key="add_ref_url_2")
    new_url_3 = st.text_input("参考图 3", placeholder="https://...", key="add_ref_url_3")
    new_url_4 = st.text_input("参考图 4", placeholder="https://...", key="add_ref_url_4")
    new_url_5 = st.text_input("参考图 5", placeholder="https://...", key="add_ref_url_5")
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认添加", type="primary"):
            if not new_car:
                st.error("❌ 车系名称不能为空")
            else:
                current_refs = dm.get_refs()
                new_id = str(len(current_refs) + 1)
                
                row = {
                    "ref_id": new_id,
                    "car": new_car,
                    "ref_url_1": new_url_1,
                    "ref_url_2": new_url_2,
                    "ref_url_3": new_url_3,
                    "ref_url_4": new_url_4,
                    "ref_url_5": new_url_5
                }
                current_refs = pd.concat([current_refs, pd.DataFrame([row])], ignore_index=True)
                dm.save_csv("ref.csv", current_refs)
                load_refs_cached.clear()
                st.toast(f"车系 {new_car} 已添加！", icon="✅")
                time.sleep(0.5)
                st.rerun()
    
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 编辑车系 ====================
@st.dialog("✏️ 编辑车系", width="medium")
def show_edit_ref_dialog(ref_data):
    edit_car = st.text_input("车系名称", value=ref_data['car'], key="edit_ref_car")
    edit_url_1 = st.text_input("参考图 1", value=ref_data.get('ref_url_1', '') or '', key="edit_ref_url_1")
    edit_url_2 = st.text_input("参考图 2", value=ref_data.get('ref_url_2', '') or '', key="edit_ref_url_2")
    edit_url_3 = st.text_input("参考图 3", value=ref_data.get('ref_url_3', '') or '', key="edit_ref_url_3")
    edit_url_4 = st.text_input("参考图 4", value=ref_data.get('ref_url_4', '') or '', key="edit_ref_url_4")
    edit_url_5 = st.text_input("参考图 5", value=ref_data.get('ref_url_5', '') or '', key="edit_ref_url_5")
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认修改", type="primary"):
            if not edit_car:
                st.error("❌ 车系名称不能为空")
            else:
                all_refs = dm.get_refs()
                idx = all_refs[all_refs['ref_id'] == ref_data['ref_id']].index
                if len(idx) > 0:
                    all_refs.loc[idx[0], 'car'] = edit_car
                    all_refs.loc[idx[0], 'ref_url_1'] = edit_url_1
                    all_refs.loc[idx[0], 'ref_url_2'] = edit_url_2
                    all_refs.loc[idx[0], 'ref_url_3'] = edit_url_3
                    all_refs.loc[idx[0], 'ref_url_4'] = edit_url_4
                    all_refs.loc[idx[0], 'ref_url_5'] = edit_url_5
                    dm.save_csv("ref.csv", all_refs)
                    load_refs_cached.clear()
                    st.toast("车系修改成功！", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
    
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 图片预览 ====================
@st.dialog("🖼️ 图片预览", width="large")
def show_preview_dialog(ref_data):
    st.markdown(f"### {ref_data['car']}")
    cols = st.columns(5)
    for i in range(1, 6):
        url = ref_data.get(f"ref_url_{i}")
        with cols[i-1]:
            if pd.notna(url) and str(url).strip().startswith("http"):
                st.image(str(url), caption=f"参考图 {i}")
            else:
                st.caption(f"参考图 {i}: 空")
    
    if st.button("关闭", type="primary"):
        st.rerun()

# ==================== 模块: 参考图管理 ====================
with st.container(border=True):
    st.caption(f"共 **{len(refs)}** 个车系")
    
    # ========== 操作按钮 ==========
    btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([1, 1, 1, 1, 2])
    
    with btn_col1:
        if st.button("➕ 新增", key="btn_add_ref"):
            show_add_ref_dialog()
    
    # 获取选中状态
    selected_rows = []
    selected_refs_data = pd.DataFrame()
    
    # ========== 表格展示 ==========
    if refs.empty:
        st.info("暂无车系数据，请点击【➕ 新增】添加")
    else:
        event = st.dataframe(
            refs,
            column_config={
                "ref_id": st.column_config.TextColumn("ID", width="small"),
                "car": st.column_config.TextColumn("车系名称", width="medium"),
                "ref_url_1": st.column_config.LinkColumn("参考图1", display_text="🔗 Link", width="small"),
                "ref_url_2": st.column_config.LinkColumn("参考图2", display_text="🔗 Link", width="small"),
                "ref_url_3": st.column_config.LinkColumn("参考图3", display_text="🔗 Link", width="small"),
                "ref_url_4": st.column_config.LinkColumn("参考图4", display_text="🔗 Link", width="small"),
                "ref_url_5": st.column_config.LinkColumn("参考图5", display_text="🔗 Link", width="small"),
            },
            hide_index=True,
            height=350,
            on_select="rerun",
            selection_mode="multi-row",
            key="ref_table_selector"
        )
        
        selected_rows = event.selection.rows
        selected_refs_data = refs.iloc[selected_rows] if selected_rows else pd.DataFrame()
    
    # 预览、编辑、删除按钮（顺序：新增、预览、编辑、删除）
    with btn_col2:
        preview_disabled = len(selected_rows) != 1
        if st.button("🖼️ 预览", disabled=preview_disabled, key="btn_preview_ref"):
            ref_to_preview = selected_refs_data.iloc[0].to_dict()
            show_preview_dialog(ref_to_preview)
    
    with btn_col3:
        edit_disabled = len(selected_rows) != 1
        if st.button("✏️ 编辑", disabled=edit_disabled, key="btn_edit_ref"):
            ref_to_edit = selected_refs_data.iloc[0].to_dict()
            show_edit_ref_dialog(ref_to_edit)
    
    with btn_col4:
        delete_disabled = len(selected_rows) == 0
        if st.button("🗑️ 删除", disabled=delete_disabled, key="btn_delete_ref"):
            st.session_state.show_ref_delete_confirm = True
    
    # 删除确认
    if st.session_state.get('show_ref_delete_confirm', False) and len(selected_rows) > 0:
        st.warning(f"⚠️ 确定要删除选中的 **{len(selected_rows)}** 个车系吗？")
        confirm_col1, confirm_col2, _ = st.columns([1, 1, 4])
        with confirm_col1:
            if st.button("✅ 确认删除", type="primary", key="confirm_delete_ref"):
                ids_to_delete = selected_refs_data['ref_id'].tolist()
                all_refs = dm.get_refs()
                all_refs = all_refs[~all_refs['ref_id'].isin(ids_to_delete)]
                # 重新编号
                all_refs = all_refs.reset_index(drop=True)
                all_refs['ref_id'] = (all_refs.index + 1).astype(str)
                dm.save_csv("ref.csv", all_refs)
                load_refs_cached.clear()
                st.session_state.show_ref_delete_confirm = False
                st.toast(f"已删除 {len(ids_to_delete)} 个车系！", icon="✅")
                time.sleep(0.5)
                st.rerun()
        with confirm_col2:
            if st.button("❌ 取消", key="cancel_delete_ref"):
                st.session_state.show_ref_delete_confirm = False
                st.rerun()
    
    # 选中状态提示
    if selected_rows:
        st.caption(f"已选择 **{len(selected_rows)}** 个车系")
