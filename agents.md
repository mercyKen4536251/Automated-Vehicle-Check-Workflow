# AGENTS.md - AI工程文档

本文档为AI助手快速理解项目context而编写。

## 项目概述

**项目名称**：自动化车辆审核工作流  
**技术栈**：Python 3.10+, Streamlit, Pandas, 火山引擎VLM API  
**核心功能**：基于VLM模型的5节点串联审图系统  

## 语言偏好

- AI对话和思考过程最好使用中文

## 快速命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run app.py

# 清除缓存
streamlit cache clear
```

## 代码规范

### 基础规范
- **语言**：Python 3.10+
- **框架**：Streamlit
- **字符串**：双引号（不用单引号）
- **命名**：
  - 函数/变量：snake_case
  - 类：PascalCase
  - 常量：UPPER_SNAKE_CASE

### 文档字符串
所有函数包含中英文文档字符串，格式如下：

```python
def function_name(param1, param2):
    """
    函数功能描述
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
    
    Returns:
        返回值说明
    """
```

### 代码分区
使用 `=` 分隔符标记代码区块：

```python
# ==================== 区块名称 ====================
# 代码内容
```

### 错误处理
返回包含"error"/"reason"字段的结构化字典：

```python
return {
    "final_pass": "error",
    "finish_at_step": 1,
    "parse_output": {"error": "错误信息"},
    "reason": "失败原因",
    "prompt_versions": {},
    "model_config": {}
}
```

### 导入规范
- 包内相对导入：`from . import module_name`
- 外部包绝对导入：`import pandas as pd`

### 数据处理
- 使用pandas操作CSV文件
- 注意处理字符串中的换行转义（`\n`）
- CSV文件使用双引号包裹字段

## 工程结构

### 核心模块 (src/)

**config_manager.py**
- 管理模型配置（多配置支持）
- 激活/切换模型配置
- 获取当前激活配置

**data_manager.py**
- CSV数据读写操作
- 测试用例管理
- 参考图库管理
- 问题标签管理
- 提示词管理

**model_client.py**
- VLM模型API调用封装
- 三个专用调用方法：
  - `call_single()`：单图判断（节点1-3）
  - `call_multi_ref()`：多参考图比对（节点4）
  - `call_compare()`：双图比对（节点5）
- JSON响应解析

**workflow_engine.py**
- 5节点串联工作流实现
- 每个节点的判定逻辑
- 工作流状态管理
- 最终结果判定（yes/no/unknown）

**history_manager.py**
- 测试历史保存/加载
- 指标计算（准确率、节点有效率）
- 历史记录查询/删除

### 页面模块 (pages/)

**manage/config.py**
- 模型配置管理（新增/编辑/删除/切换）
- 问题标签管理（新增/编辑/删除）
- 使用expander和dialog组件

**manage/prompt.py**
- 提示词版本管理
- 提示词激活/切换
- 提示词预览

**manage/ref_gallery.py**
- 参考图库管理（新增/编辑/删除/预览）
- 支持最多5张参考图
- 使用dialog弹窗编辑

**manage/test_cases.py**
- 测试用例管理（新增/编辑/删除/预览）
- 多维度筛选（车系/类型/标签）
- goodcase不能选择标签

**test/run_test.py**
- 批量测试执行
- 多线程并发处理（最多10个）
- 实时进度显示
- 多维度筛选
- 结果保存到session_state

**test/result.py**
- 测试记录展示
- 详细结果分析
- 多维度筛选
- 配置信息展示

## 关键业务逻辑

### 工作流最终结果

- `final_pass="yes"`：通过所有审核
- `final_pass="no"`：在某个节点被明确判定为不合格
- `final_pass="unknown"`：无法判定（如Node4找不到匹配视角）

### 审图准确率判定

- **badcase**：`final_pass="no"` 才算正确
- **goodcase**：`final_pass="yes"` 才算正确
- **unknown**：无论哪种都算错误

### 节点有效率定义

- **分母**：所有case总数
- **分子**：在预期节点被正确处理的case数
  - badcase：`final_pass="no"` 且在预期节点被过滤
  - goodcase：`final_pass="yes"` 且经过节点5

### 图片传递顺序

- **Node1-3**：仅生成图
- **Node4**：参考图在前，生成图在后
- **Node5**：参考图+描述+生成图

## 数据结构

### problem_tags.csv
```
tag_id, tag_content, expected_filter_node
1, 非汽车, 1
2, 存在汽车但不可用, 1
3, 裁切, 2
...
```

### test_cases.csv
```
case_id, car, case_type, problem_tag, case_url
1, 问界M8, badcase, 裁切, https://...
2, 问界M8, goodcase, , https://...
```

### test_history/{test_id}.json
```json
{
  "test_id": "20250114_120000",
  "test_time": "2025-01-14 12:00:00",
  "cases_total": 10,
  "acc_total": 8,
  "acc_rate": 0.8,
  "node_efficiency": 0.75,
  "results": [...]
}
```

## UI组件使用规范

### 按钮顺序
管理页面按钮顺序统一为：新增 → 预览 → 编辑 → 删除

### Dialog弹窗
- 新增/编辑：使用dialog弹窗
- 宽度：`width="medium"`
- 确认/取消按钮：2列布局

### 表格选择
- 使用 `st.dataframe` + `on_select="rerun"` + `selection_mode="multi-row"`
- 预览/编辑：单选（多选时按钮禁用）
- 删除：支持批量

### 筛选器
- 使用 `st.multiselect` 实现多选筛选
- 布局：1:1:1 或 1:1:1:1
- 逻辑：AND关系

### 容器布局
- 外层：`st.container(border=True)`
- 不要额外包裹tab内容

## 常见问题

### 关于goodcase
- goodcase没有问题标签
- 在标签选择时，选择goodcase会禁用标签选择框
- goodcase必须走完5个节点且`final_pass="yes"`才算精准

### 关于图片顺序
- Node4的`match_image`返回值是参考图的顺序（1-N）
- 不是整体图片列表的索引

### 关于缓存
- 使用 `@st.cache_data(ttl=300)` 缓存数据
- 修改数据后需要调用 `.clear()` 清除缓存

## 版本管理

详见 [VERSION.md](../VERSION.md)

当前版本：v1.5.0（2025-01-14）

## 相关文档

- [README.md](../README.md) - 项目文档
- [VERSION.md](../VERSION.md) - 版本历史
- [LICENSE](../LICENSE) - 许可证

