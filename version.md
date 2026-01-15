# 版本历史

## v2.0.0（2025-01-15）

**架构重构 - 前后端分离**:
- 引入 FastAPI 后端，实现真正的前后端分离架构
- 后端使用 BackgroundTasks 实现异步任务执行
- 前端通过 RESTful API 与后端通信
- 任务在后台执行，不阻塞 UI，用户可自由操作

**运行中心重大升级**:
- 实现累积选择功能：支持跨筛选条件累积勾选用例
- 任务提交后在后台执行，用户可继续操作（切换页面、勾选新用例）
- 实时任务监控：显示进度条、当前执行用例、完成/失败数量
- 支持任务取消功能
- 任务完成后自动清空选择，准备下一轮测试

**目录结构优化**:
- 创建 `data/prompts/` 目录，统一管理提示词文件
- 移动 `app.py` 到 `pages/` 目录，结构更清晰
- 新增 `backend/` 目录，包含完整的后端代码
- 新增 `start.py` 一键启动脚本

**后端架构**:
- `backend/main.py`: FastAPI 主入口
- `backend/api/models.py`: Pydantic 数据模型
- `backend/api/routes/test.py`: 测试任务 API 路由
- `backend/tasks/manager.py`: 任务管理器（单例模式）
- `backend/tasks/executor.py`: 任务执行器

**API 接口**:
- `POST /api/test/submit`: 提交测试任务
- `GET /api/test/status/{task_id}`: 查询任务状态
- `POST /api/test/cancel/{task_id}`: 取消任务
- `GET /api/test/tasks`: 获取任务列表
- `GET /api/test/stats`: 获取任务统计
- `GET /health`: 健康检查

**启动方式变更**:
- 旧版：`streamlit run app.py`
- 新版：`python start.py`（自动启动后端+前端）
- 后端 API: http://localhost:8000
- 前端界面: http://localhost:8501
- API 文档: http://localhost:8000/docs

**依赖更新**:
- 新增 `fastapi>=0.104.0`
- 新增 `uvicorn>=0.24.0`
- 新增 `pydantic>=2.5.0`
- 新增 `requests>=2.31.0`

**未来扩展性**:
- 预留升级到 Celery + Redis 的架构空间
- 支持多用户、任务队列、定时任务等高级功能
- 可轻松添加更多 API 接口

## v1.5.0（2025-01-14）

**运行中心UI优化**:
- 移除逐行日志展示，改为动态单行状态显示
- 使用 `st.empty()` 实现实时状态更新
- 状态格式：`✅ 正在处理 Case 1 (问界M8) - 1/10`

**审图准确率判断逻辑调整**:
- badcase：`final_pass="no"` 才算正确（严格）
- goodcase：`final_pass="yes"` 或 `final_pass="unknown"` 都算正确（宽松）
- 原因：goodcase的unknown表示无法判定（如缺少参考图），不是图片本身的问题

**结果面板metric实时计算**:
- 将筛选器移到配置信息下方
- metric计算基于筛选后的数据，而非全量数据
- 筛选条件变化时，metric自动重新计算
- metric位置保持不变（筛选器下方）

**前端数据处理优化**:
- 在前端重新计算 `is_correct`，使用新逻辑
- 兼容历史数据，即使旧数据也能正确显示新逻辑的结果
- 确保审图准确率和节点有效率的区别正确体现

**节点有效率保持严格标准**:
- badcase：`final_pass="no"` 且在预期节点被过滤
- goodcase：`final_pass="yes"` 且经过节点5
- 不受审图准确率宽松逻辑影响

## v1.4.0（2025-01-14）

**模型客户端重构**:
- 将通用 `call()` 方法拆分为3个专用方法：`call_single()`、`call_multi_ref()`、`call_compare()`
- 优化消息结构，明确区分参考图和生成图
- 提高代码可维护性和业务逻辑清晰度

**工作流引擎优化**:
- 节点1-3：使用 `call_single()` 进行单图判断
- 节点4：使用 `call_multi_ref()` 进行多参考图比对，参考图在前、生成图在后
- 节点5：使用 `call_compare()` 进行双图比对，自动处理描述占位符
- 修正 `match_image` 解析逻辑，模型返回1-N直接对应参考图1-N

**节点有效率指标完善**:
- 重新定义节点有效率：分母为所有case总数，分子为在预期节点被正确处理的case数
- badcase：`final_pass="no"` 且在预期节点被过滤才算精准
- goodcase：`final_pass="yes"` 且经过节点5才算精准
- `final_pass="unknown"` 的case无论哪种都算节点不精准

**结果面板重构**:
- 改用 `st.tabs` 实现测试记录和详细结果的分离展示
- 测试记录中每条记录支持「查看详情」和「删除」操作
- 详细结果中新增配置信息展示（模型、思考模式、提示词版本）
- 优化详细列表布局：3列展示（基础信息、图片预览、模型输出JSON）
- 新增多维度筛选（结果/车系/类型/标签）

**其他改进**:
- 确保goodcase在标签管理中被正确处理（无标签）
- 完善审图准确率判断逻辑，适配final_pass三态（yes/no/unknown）

## v1.3.0（2025-01-14）

**数据结构优化**:
- 新增 `expected_filter_node` 字段到 `problem_tags.csv`，标记每个标签预期在哪个节点被过滤

**数据管理模块**:
- `add_problem_tag()` 支持传入 `expected_filter_node`
- `update_problem_tag()` 支持更新 `expected_filter_node`
- 新增 `get_expected_filter_node()` 函数

**配置管理页面**:
- 标签展示包含预期过滤节点信息
- 新增/编辑标签时可选择预期过滤节点（下拉选择1-5）

**历史管理模块**:
- `save_test_history()` 接收 `tag_node_map` 参数
- 新增指标：`badcase_total`、`badcase_correct`、`precise_total`、`node_efficiency`
- 每条结果新增 `is_precise` 和 `expected_filter_node` 字段

**运行测试页面**:
- 保存历史时传入标签到节点的映射

**结果面板**:
- 新增"节点有效率"指标展示
- 新增"节点不精准"筛选选项
- 列表中显示节点信息，不精准的标记 ⚠️
- 历史记录也显示节点有效率

## v1.2.0 (2025-01-13)

**参考图库管理**:
- 新增弹窗式新增、编辑、预览功能
- 改用多选表格，支持批量删除
- 添加删除确认机制
- 优化操作按钮布局

**测试用例管理**:
- 新增弹窗式新增、编辑、预览功能
- 新增多维度筛选（车系、类型、标签）
- 改用多选表格，支持批量删除
- 添加删除确认机制
- 新增用例时继承最后一条数据的默认值

**运行中心**:
- 新增多维度筛选（车系、类型、标签）
- 改用多选表格，优化用例选择流程

## v1.1.0 (2025-01-12)

**界面逻辑优化**:
- 优化整体界面布局和交互逻辑
- 改进用户体验和操作流程

## v1.0.0 (2025-01-12)

**初始版本发布**

**核心功能**:
- 实现5节点审图工作流
- 支持模型配置管理（多配置支持）
- 支持提示词版本管理
- 支持参考图库管理
- 支持测试用例管理
- 支持批量测试执行（并发）
- 支持测试结果统计和历史记录
