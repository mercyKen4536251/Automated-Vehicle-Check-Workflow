# 自动化车辆审核工作流 (Automated Vehicle Check Workflow)

**当前版本：v1.0.0**

|[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
|[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-orange.svg)](https://streamlit.io/)
|[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


## 项目结构

```
├── home.py                 # 主页入口
├── requirements.txt        # 项目依赖
├── README.md              # 项目说明文档
├── SETUP.md               # 安装配置指南
├── pages/                # 功能页面目录
│   ├── 1_提示词管理.py
│   ├── 2_参考图库管理.py
│   ├── 3_测试用例管理.py
│   ├── 4_运行中心.py
│   └── 5_结果面板.py
├── src/                  # 核心逻辑模块
│   ├── config_manager.py   # 配置管理
│   ├── data_manager.py     # 数据管理
│   ├── history_manager.py  # 历史记录管理
│   ├── model_client.py     # 模型客户端
│   └── workflow_engine.py  # 工作流引擎
└── data/                 # 数据存储目录
    ├── model_config.csv    # 模型配置（敏感，已加入.gitignore）
    ├── prompt_01.csv ~ prompt_05.csv  # 5个节点的提示词
    ├── ref.csv             # 参考图库
    ├── test_cases.csv      # 测试用例
    ├── problem_tags.csv    # 问题标签
    └── test_history/       # 测试历史记录
```

## 核心功能

### 1. 模型配置管理
- 支持多模型配置管理
- 配置包括：模型ID、API Key、思考模式
- 支持激活配置（切换使用不同模型）
- 配置持久化存储

### 2. 提示词管理
- 管理5个智能体节点对应的提示词
- 支持提示词版本管理
- 可编辑和更新各节点提示词内容

### 3. 参考图库管理
- 管理不同车系的标准参考图
- 每个车系最多支持5张参考图
- 支持图片预览功能

### 4. 测试用例管理
- 管理待审核的测试用例
- 支持badcase/goodcase分类
- 可标注问题类型和关联车系

### 5. 自动化测试运行
- 实现5节点审图工作流
- 支持单例测试、批量测试、全量测试选项
- 一票否决机制（任意节点失败则停止）

### 6. 结果看板
- 展示测试结果统计
- 提供准确率分析
- 支持历史测试记录查看

## 审图工作流概述

1. **Node 1 - 汽车检测**: 判断图片中是否存在汽车 (car="yes"才通过)
2. **Node 2 - 裁切检测**: 判断车身是否被裁切 (cropping="no"才通过)
3. **Node 3 - 运动/无人驾驶检测**: 判断是否为运动状态或无人驾驶 (match="yes"才通过)
4. **Node 4 - 视角一致性**: 判断生成图与参考图视角是否一致 (match="yes"才通过)
5. **Node 5 - 细节一致性**: 判断生成图与参考图细节是否一致 (match="yes"才通过)

## Quick Start

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **启动应用**：
   ```bash
   streamlit run home.py
   ```

3. **配置API Key**：
   - 首次运行后，访问首页"模型配置管理"
   - 点击"➕ 添加配置"，输入火山引擎API Key
   - 详细的配置说明请查看 [SETUP.md](SETUP.md)

## 版本历史

### v1.0.0 (2025-01-12)
- ✅ 初始版本发布
- ✅ 实现5节点审图工作流
- ✅ 支持模型配置管理
- ✅ 支持提示词版本管理
- ✅ 支持参考图库管理
- ✅ 支持测试用例管理
- ✅ 支持批量测试执行
- ✅ 支持测试结果统计和历史记录