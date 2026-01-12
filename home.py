import streamlit as st
import sys
import os
import time

# 添加src到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import config_manager as cm

st.set_page_config(
    page_title="AVCW - Automated Vehicle Check Workflow",
    page_icon="🚗",
    layout="wide"
)
st.title("🚗 AVCW - Automated Vehicle Check Workflow")

# ==================== 系统功能介绍 ====================
st.markdown("---")
st.markdown("### 🚀 系统功能介绍")
st.info("👋 欢迎使用 AVCW 自动审核平台！请从左侧导航栏选择功能模块。")
st.markdown("""
- **🧩 提示词管理**: 管理和优化工作各个节点的审核提示词。
- **🖼️ 参考图库管理**: 管理不同车系的标准参考图。
- **📋 测试用例管理**: 管理待审核的测试用例。
- **🚀 运行中心**: 执行自动化测试。
- **📊 结果面板**: 查看测试结果统计与详细报告。
""")

# ==================== 模型配置管理 ====================
st.markdown("---")
st.markdown("### ⚙️ 模型配置管理")

# 获取当前配置
try:
    active_config = cm.get_active_config()
    all_configs = cm.get_all_configs()
    
    # 显示当前激活的配置
    st.success(f"✅ 当前使用配置：**{active_config['model_id']}** (thinking_mode: {active_config['thinking_mode']})")
    
    with st.container(border=True):
        # Tab切换
        tab1, tab2 = st.tabs(["📋 配置列表", "➕ 添加配置"])
        
        # ==================== Tab1: 配置列表 ====================
        with tab1:
            st.markdown("当前模型配置情况：")
            
            if not all_configs.empty:
                for idx, row in all_configs.iterrows():
                    is_first = (idx == 0)  # 第一个配置即为激活配置
                    
                    with st.expander(
                        f"{'🟢' if is_first else '⚪'} {row['model_id']} (thinking_mode: {row['thinking_mode']})",
                        expanded=is_first
                    ):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**配置ID:** `{row['config_id']}`")
                            st.markdown(f"**模型ID:** {row['model_id']}")
                            st.markdown(f"**API Key:** `{row['api_key'][:20]}...`")
                            st.markdown(f"**think mode:** {row['thinking_mode']}")
                            st.markdown(f"**状态:** {'🟢 激活中' if is_first else '⚪ 未激活'}")
                        
                        with col2:
                            if not is_first:
                                if st.button("激活", key=f"activate_{row['config_id']}"):
                                    if cm.set_active_config(row['config_id']):
                                        st.toast("✅ 配置已激活！", icon="✅")
                                        time.sleep(0.8)
                                        st.rerun()
                                    else:
                                        st.error("❌ 激活失败")
                            
                            if len(all_configs) > 1:
                                if st.button("删除", key=f"delete_{row['config_id']}", type="secondary"):
                                    if cm.delete_config(row['config_id']):
                                        st.toast("✅ 配置已删除！", icon="✅")
                                        time.sleep(0.8)
                                        st.rerun()
                                    else:
                                        st.error("❌ 无法删除（至少保留一个配置）")
            else:
                st.info("暂无配置")
        
        # ==================== Tab2: 添加配置 ====================
        with tab2:
            st.markdown("### 添加新配置")
            
            # 使用session_state来控制表单重置
            if 'config_form_key' not in st.session_state:
                st.session_state.config_form_key = 0
            
            with st.form(key=f"add_config_form_{st.session_state.config_form_key}"):
                new_model_id = st.text_input(
                    "模型ID *",
                    placeholder="doubao-seed-1-8-251228",
                    help="火山引擎模型ID"
                )
                
                new_api_key = st.text_input(
                    "API Key *",
                    type="password",
                    placeholder="输入API密钥",
                    help="火山引擎API密钥"
                )
                
                new_thinking_mode = st.selectbox(
                    "思考模式",
                    options=cm.get_thinking_mode_options(),
                    help="是否开启模型思考模式"
                )
                
                submitted = st.form_submit_button("➕ 添加配置", type="primary")
                
                if submitted:
                    if not new_model_id or not new_api_key:
                        st.error("❌ 模型ID和API Key不能为空")
                    else:
                        config_id = cm.add_config(
                            model_id=new_model_id,
                            api_key=new_api_key,
                            thinking_mode=new_thinking_mode
                        )
                        st.toast("✅ 配置已添加！", icon="✅")
                        # 重置表单
                        st.session_state.config_form_key += 1
                        time.sleep(0.8)
                        st.rerun()

except Exception as e:
    st.error(f"❌ 加载配置失败: {e}")
