import streamlit as st
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from src import data_manager as dm

# ==================== 缓存函数 ====================
@st.cache_data(ttl=300)
def load_prompts_cached():
    return dm.get_prompts()

@st.cache_data(ttl=300)
def load_prompt_versions_cached(node_index):
    return dm.get_prompt_versions(node_index)

# ==================== 页面标题 ====================
st.header("🧩 提示词管理")
st.markdown("---")

# ==================== 节点选项 ====================
NODE_OPTIONS = {
    1: "节点1: 是否存在汽车",
    2: "节点2: 是否裁切",
    3: "节点3: 运动/无人驾驶",
    4: "节点4: 视角一致性",
    5: "节点5: 细节一致性"
}

# ==================== 节点选择与当前激活信息 ====================
with st.container(border=True):
    # 节点选择器
    selected_node_idx = st.selectbox(
        "选择节点提示词",
        options=list(NODE_OPTIONS.keys()),
        format_func=lambda x: NODE_OPTIONS[x],
        key="node_select"
    )
    
    # 加载当前节点的激活提示词
    prompts = load_prompts_cached()
    current_data = prompts.get(selected_node_idx, {})
    active_version = current_data.get('prompt_version', "无")
    
    # 显示当前激活版本信息
    st.info(f"✅ 当前激活版本: {active_version}")

st.write("")

# ==================== 版本号输入弹窗 ====================
@st.dialog("💾 保存提示词", width="medium")
def show_save_dialog():
    # 获取待保存的内容
    pending_content = st.session_state.get('pending_content', '')
    pending_selected_version = st.session_state.get('pending_selected_version', 'v1.0.0')

    # 版本号输入
    new_version = st.text_input(
        "请输入版本号：",
        value=pending_selected_version,
        help="使用已有版本号 = 更新内容；使用新版本号 = 创建新版本"
    )

    # 操作按钮
    col_confirm, col_cancel = st.columns([1, 1])

    with col_confirm:
        if st.button("✅ 确认保存", type="primary"):
            if new_version and pending_content:
                operation_type, saved_version = dm.update_prompt(
                    selected_node_idx,
                    pending_content,
                    new_version
                )
                # 清除缓存
                load_prompts_cached.clear()
                load_prompt_versions_cached.clear()
                # 更新选中版本
                st.session_state[f'edit_version_{selected_node_idx}'] = saved_version
                # 清除 session_state
                st.session_state.pop('pending_content', None)
                st.session_state.pop('pending_selected_version', None)

                if operation_type == 'update':
                    st.toast(f"版本 {saved_version} 已更新！", icon="✅")
                else:
                    st.toast(f"已创建新版本 {saved_version}！", icon="✅")

                time.sleep(0.5)
                st.rerun()  # 关闭对话框
            else:
                st.error("版本号不能为空")

    with col_cancel:
        if st.button("❌ 取消"):
            # 清除 session_state
            st.session_state.pop('pending_content', None)
            st.session_state.pop('pending_selected_version', None)
            st.rerun()  # 关闭对话框

# ==================== 模块: 提示词内容编辑 ====================
with st.container(border=True):
    # 加载所有版本
    all_versions = load_prompt_versions_cached(selected_node_idx)
    
    # 初始化选中版本状态
    version_state_key = f'edit_version_{selected_node_idx}'
    if version_state_key not in st.session_state:
        st.session_state[version_state_key] = active_version

    if not all_versions.empty:
        version_list = all_versions['prompt_version'].tolist()
        # 构建版本标签（标记激活状态）
        version_labels = []
        for _, row in all_versions.iterrows():
            label = row['prompt_version']
            if row['is_active']:
                label += " ✅"
            version_labels.append(label)
        
        # 确保选中版本有效
        if st.session_state[version_state_key] not in version_list:
            st.session_state[version_state_key] = version_list[0] if version_list else active_version
        
        # 版本选择下拉框
        selected_idx = version_list.index(st.session_state[version_state_key]) if st.session_state[version_state_key] in version_list else 0
        
        # 定义回调函数
        def on_version_change():
            selected_label = st.session_state[f"version_select_{selected_node_idx}"]
            selected_version = selected_label.replace(" ✅", "")
            st.session_state[version_state_key] = selected_version
        
        selected_label = st.selectbox(
            "选择要编辑的版本",
            options=version_labels,
            index=selected_idx,
            key=f"version_select_{selected_node_idx}",
            on_change=on_version_change
        )
        
        # 解析选中的版本号
        selected_version = selected_label.replace(" ✅", "")
        
        # 获取选中版本的内容
        selected_data = all_versions[all_versions['prompt_version'] == selected_version]
        if not selected_data.empty:
            edit_content = selected_data.iloc[0]['prompt_content']
            is_active = selected_data.iloc[0]['is_active']
        else:
            edit_content = ""
            is_active = False
    else:
        selected_version = "v1.0.0"
        edit_content = ""
        is_active = False
        st.info("暂无版本记录")

    # 提示词内容编辑区（使用唯一key确保内容更新）
    content_key = f"edit_content_{selected_node_idx}_{st.session_state.get(version_state_key, 'default')}"
    new_content = st.text_area(
        "提示词内容",
        value=edit_content if 'edit_content' in dir() else "",
        height=500,
        key=content_key
    )
    
    # 操作按钮
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("💾 保存", key=f"save_btn_{selected_node_idx}"):
            if not new_content:
                st.toast("提示词内容不能为空", icon="❌")
            else:
                # 设置待保存的内容到 session_state
                st.session_state.pending_content = new_content
                st.session_state.pending_selected_version = selected_version
                # 调用原生对话框函数
                show_save_dialog()
    
    with col_btn2:
        # 激活按钮（仅当版本未激活时显示）
        if 'is_active' in dir() and not is_active and 'selected_version' in dir():
            if st.button(f"🔄 激活此版本", key=f"activate_btn_{selected_node_idx}"):
                if dm.activate_prompt_version(selected_node_idx, selected_version):
                    load_prompts_cached.clear()
                    load_prompt_versions_cached.clear()
                    st.toast(f"已激活版本 {selected_version}！", icon="✅")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.toast("激活失败", icon="❌")
        # 当版本已激活时，不显示任何内容（删除原来的caption）
