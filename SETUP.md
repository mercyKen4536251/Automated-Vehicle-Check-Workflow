# 安装和配置指南

## 首次使用配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API Key

首次运行时，需要配置火山引擎的API Key：

1. 访问[火山引擎控制台](https://console.volcengine.com/ark)
2. 获取API Key
3. 运行应用后，在首页"模型配置管理"中：
   - 点击"➕ 添加配置"
   - 输入模型ID和API Key
   - 保存配置

### 3. 数据目录说明

首次运行后，会在`data/`目录下创建以下文件：

- `model_config.csv` - 模型配置（包含API Key，**不要提交到Git**）
- `prompt_01.csv` ~ `prompt_05.csv` - 5个节点的提示词
- `ref.csv` - 参考图库
- `test_cases.csv` - 测试用例
- `problem_tags.csv` - 问题标签
- `test_history/` - 测试历史记录

## 运行应用

```bash
streamlit run home.py
```

## 注意事项

- ⚠️ `data/model_config.csv`包含敏感信息，已加入.gitignore，不会提交到版本库
- ⚠️ 提交代码前，请确保不要包含真实的API Key
- 📝 所有配置文件都会在首次运行时自动创建
