# AGENTS.md

## 语言偏好
- 所有文档、注释、回复使用中文
- AI对话和思考过程使用中文

## 命令
- 安装: `pip install -r requirements.txt`
- 运行: `streamlit run app.py`
- 无测试框架 - 通过UI手动测试

## 代码规范
- 语言: Python 3.10+, Streamlit框架
- 文档字符串: 中文，包含Args/Returns说明
- 命名: snake_case（函数/变量），PascalCase（类）
- 字符串: 双引号
- 代码分区: 使用 `=` 分隔符（如 `# ====================`）
- 错误处理: 返回包含"error"/"reason"字段的结构化字典
- 导入: 包内相对导入（`from . import x`），外部包绝对导入
- 数据处理: 使用pandas操作CSV，注意处理字符串中的换行转义
