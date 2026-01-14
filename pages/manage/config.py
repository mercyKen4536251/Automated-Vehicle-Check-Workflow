import streamlit as st
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src import config_manager as cm
from src import data_manager as dm

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_model_configs_cached():
    return cm.get_all_configs()

@st.cache_data(ttl=300)
def load_problem_tags_cached():
    return dm.get_problem_tags()

# ==================== 页面标题 ====================
st.header("⚙️ 配置管理")
st.markdown("---")

# 加载数据
configs = load_model_configs_cached()
tags_df = load_problem_tags_cached()
tag_list = tags_df['tag_content'].tolist() if not tags_df.empty else []

# 节点选项
NODE_OPTIONS = {
    1: "节点1: 存在性/可用性",
    2: "节点2: 裁切检测",
    3: "节点3: 车牌有字/无人驾驶",
    4: "节点4: 视角一致性",
    5: "节点5: 细节一致性"
}

# ==================== Dialog: 新增模型 ====================
@st.dialog("➕ 新增模型配置", width="medium")
def show_add_model_dialog():
    new_model_id = st.text_input("模型ID", placeholder="例如: doubao-seed-1-8-251228", key="new_model_id")
    new_api_key = st.text_input("API Key", type="password", key="new_api_key")
    new_thinking = st.selectbox("思考模式", ["disabled", "enabled"], key="new_thinking")
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认添加", type="primary"):
            if not new_model_id or not new_api_key:
                st.error("模型ID和API Key不能为空")
            else:
                cm.add_config(new_model_id, new_api_key, new_thinking)
                load_model_configs_cached.clear()
                st.toast("模型配置添加成功！", icon="✅")
                time.sleep(0.5)
                st.rerun()
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 编辑模型 ====================
@st.dialog("✏️ 编辑模型配置", width="medium")
def show_edit_model_dialog(config_data):
    edit_model_id = st.text_input("模型ID", value=config_data['model_id'], key="edit_model_id")
    edit_api_key = st.text_input("API Key", value=config_data['api_key'], type="password", key="edit_api_key")
    edit_thinking = st.selectbox(
        "思考模式", 
        ["disabled", "enabled"], 
        index=0 if config_data['thinking_mode'] == 'disabled' else 1,
        key="edit_thinking"
    )
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认修改", type="primary"):
            if not edit_model_id or not edit_api_key:
                st.error("模型ID和API Key不能为空")
            else:
                cm.update_config(
                    config_data['config_id'],
                    model_id=edit_model_id,
                    api_key=edit_api_key,
                    thinking_mode=edit_thinking
                )
                load_model_configs_cached.clear()
                st.toast("模型配置修改成功！", icon="✅")
                time.sleep(0.5)
                st.rerun()
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 新增标签 ====================
@st.dialog("➕ 新增标签", width="medium")
def show_add_tag_dialog():
    new_tag = st.text_input("标签名称", placeholder="例如: 裁切、车牌文字...", key="new_tag_name")
    new_node = st.selectbox(
        "预期过滤节点",
        options=list(NODE_OPTIONS.keys()),
        format_func=lambda x: NODE_OPTIONS[x],
        key="new_tag_node"
    )
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认添加", type="primary"):
            if not new_tag:
                st.error("标签名称不能为空")
            elif new_tag in tag_list:
                st.error("标签已存在")
            else:
                dm.add_problem_tag(new_tag, new_node)
                load_problem_tags_cached.clear()
                st.toast("标签添加成功！", icon="✅")
                time.sleep(0.5)
                st.rerun()
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 编辑标签 ====================
@st.dialog("✏️ 编辑标签", width="medium")
def show_edit_tag_dialog():
    tag_to_edit = st.selectbox("选择标签", tag_list, key="select_tag_to_edit")
    tag_row = tags_df[tags_df['tag_content'] == tag_to_edit].iloc[0]
    
    new_tag_content = st.text_input("标签名称", value=tag_to_edit, key="edit_tag_content")
    
    current_node = int(tag_row['expected_filter_node']) if 'expected_filter_node' in tag_row else 1
    new_node = st.selectbox(
        "选择过滤节点",
        options=list(NODE_OPTIONS.keys()),
        format_func=lambda x: NODE_OPTIONS[x],
        index=current_node - 1,
        key="edit_tag_node"
    )
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认修改", type="primary"):
            if not new_tag_content:
                st.error("标签名称不能为空")
            else:
                dm.update_problem_tag(tag_row['tag_id'], new_tag_content, new_node)
                load_problem_tags_cached.clear()
                st.toast("标签修改成功！", icon="✅")
                time.sleep(0.5)
                st.rerun()
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== Dialog: 删除标签 ====================
@st.dialog("🗑️ 删除标签", width="medium")
def show_delete_tag_dialog():
    tag_to_delete = st.selectbox("选择要删除的标签", tag_list, key="select_tag_to_delete")
    tag_row = tags_df[tags_df['tag_content'] == tag_to_delete].iloc[0]
    
    st.warning(f"⚠️ 确定要删除标签 `{tag_to_delete}` 吗？")
    
    col_confirm, col_cancel = st.columns([1, 1])
    with col_confirm:
        if st.button("✅ 确认删除", type="primary"):
            dm.delete_problem_tag(tag_row['tag_id'])
            load_problem_tags_cached.clear()
            st.toast("标签已删除！", icon="✅")
            time.sleep(0.5)
            st.rerun()
    with col_cancel:
        if st.button("❌ 取消"):
            st.rerun()

# ==================== 模块1: 模型配置 ====================
with st.expander("🤖 模型配置", expanded=True):
    if configs.empty:
        st.warning("暂无模型配置")
    else:
        # 当前激活的配置（第一行）
        active_config = configs.iloc[0]
        
        st.info(f"**当前模型:** `{active_config['model_id']}`　　**思考模式:** `{active_config['thinking_mode']}`")
        
        # 如果有多个配置，显示切换下拉框
        if len(configs) > 1:
            config_options = configs['model_id'].tolist()
            
            selected_model = st.selectbox(
                "切换模型",
                config_options,
                index=0,
                key="model_select"
            )
            
            if selected_model != active_config['model_id']:
                selected_config = configs[configs['model_id'] == selected_model].iloc[0]
                if st.button("✅ 确认切换", key="confirm_switch_model"):
                    cm.set_active_config(selected_config['config_id'])
                    load_model_configs_cached.clear()
                    st.toast(f"已切换到 {selected_model}", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
        
        # 操作按钮
        btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 3])
        
        with btn_col1:
            if st.button("➕ 新增", key="btn_add_model"):
                show_add_model_dialog()
        
        with btn_col2:
            if st.button("✏️ 编辑", key="btn_edit_model"):
                show_edit_model_dialog(active_config.to_dict())
        
        with btn_col3:
            delete_disabled = len(configs) <= 1
            if st.button("🗑️ 删除", disabled=delete_disabled, key="btn_delete_model", help="至少保留一个配置"):
                st.session_state.show_delete_model = True
        
        # 删除确认
        if st.session_state.get('show_delete_model', False):
            st.warning(f"⚠️ 确定要删除当前模型配置 `{active_config['model_id']}` 吗？")
            col1, col2, _ = st.columns([1, 1, 4])
            with col1:
                if st.button("✅ 确认删除", type="primary", key="confirm_delete_model"):
                    cm.delete_config(active_config['config_id'])
                    load_model_configs_cached.clear()
                    st.session_state.show_delete_model = False
                    st.toast("模型配置已删除！", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
            with col2:
                if st.button("❌ 取消", key="cancel_delete_model"):
                    st.session_state.show_delete_model = False
                    st.rerun()

st.write("")

# ==================== 模块2: 问题标签 ====================
with st.expander("🏷️ 问题标签", expanded=True):
    if tags_df.empty:
        st.info("暂无问题标签")
    else:
        # 构建标签展示列表（包含预期节点信息）
        tag_display_list = []
        for _, row in tags_df.iterrows():
            node = int(row['expected_filter_node']) if 'expected_filter_node' in row else 0
            node_name = NODE_OPTIONS.get(node, "未知")
            tag_display_list.append(f"{row['tag_content']} → {node_name}")
        
        # 标签数量提示
        st.info(f"共 **{len(tag_list)}** 个标签")

        # 下拉框展示标签
        st.selectbox(
            "查看标签列表",
            tag_display_list,
            key="tag_view",
        )
    
    # 操作按钮
    btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 3])
    
    with btn_col1:
        if st.button("➕ 新增", key="btn_add_tag"):
            show_add_tag_dialog()
    
    with btn_col2:
        edit_tag_disabled = tags_df.empty
        if st.button("✏️ 编辑", disabled=edit_tag_disabled, key="btn_edit_tag"):
            show_edit_tag_dialog()
    
    with btn_col3:
        delete_tag_disabled = len(tags_df) <= 1
        if st.button("🗑️ 删除", disabled=delete_tag_disabled, key="btn_delete_tag", help="至少保留一个标签"):
            show_delete_tag_dialog()
