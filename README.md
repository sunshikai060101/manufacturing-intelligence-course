# 智能仓储物料识别与分拣系统

> 基于机器视觉与多传感器融合的智能仓储物料识别与分拣系统
>
> 《制造智能技术》课程设计项目

## 项目简介

本项目面向智能仓储物料分拣场景，综合运用机器视觉、深度学习、多传感器数据融合及工业数据分析等技术，实现仓储物料的智能识别、多维度校验、异常检测与库存管理。系统采用B/S架构，提供完整的Web可视化操作界面。

### 核心功能

- **物料智能识别**：基于YOLO目标检测算法，支持6类仓储物料的实时识别与定位
- **多传感器融合**：融合视觉信息与重量传感器、红外传感器数据，进行一致性校验
- **异常检测**：基于统计学习的多维度异常分析（置信度、尺寸、频率、重量）
- **库存管理**：入库、出库、库存预警、库存查询等完整库存管理功能
- **数据可视化**：仪表盘统计、类别分布、趋势分析、检测记录管理

### 技术方向覆盖

| 技术方向 | 课程章节 | 应用模块 |
|----------|----------|----------|
| 机器视觉与图像处理 | 机器视觉技术 | 图像预处理、目标检测 |
| 深度学习与人工智能 | 深度学习与人工智能 | YOLO检测算法 |
| 传感器与检测技术 | 传感器与检测技术 | 多传感器融合 |
| 数据分析与挖掘 | 工业数据分析 | 异常检测、统计分析 |

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      表现层（前端）                         │
│  仪表盘 │ 物料检测 │ 库存管理 │ 传感器数据 │ 检测记录 │ 设置 │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP/RESTful API
┌──────────────────────────▼──────────────────────────────┐
│                      业务层（后端）                         │
│  检测服务 │ 库存服务 │ 传感器服务 │ 统计服务 │ 配置管理    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                      算法层                                │
│  目标检测(YOLO) │ 多传感器融合 │ 异常检测(统计学习)       │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                      数据层                                │
│  SQLite数据库 │ 图像文件存储 │ 模型文件 │ 配置文件        │
└─────────────────────────────────────────────────────────┘
```

## 技术栈

### 后端
- **Web框架**：FastAPI 0.104+
- **数据库**：SQLite 3 + SQLAlchemy 2.0
- **数据验证**：Pydantic 2.0+
- **编程语言**：Python 3.10+
- **图像处理**：OpenCV / Pillow
- **目标检测**：Ultralytics YOLOv8（可选，支持模拟模式）

### 前端
- **标记语言**：HTML5
- **样式**：CSS3（原生，响应式设计）
- **交互**：JavaScript ES6+（原生，无框架依赖）
- **图表**：Canvas API（原生绘图）

### 开发工具
- **版本控制**：Git
- **测试框架**：pytest
- **API文档**：FastAPI自动生成（Swagger UI）

## 快速开始

### 环境要求

- Python 3.10 或更高版本
- pip 包管理器
- 现代Web浏览器（Chrome、Edge、Firefox）

### 安装步骤

1. **克隆或下载项目**
   ```bash
   cd smart-warehouse-system
   ```

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **初始化数据库**
   ```bash
   python scripts/init_db.py
   ```

4. **启动系统**
   ```bash
   python run.py
   ```

5. **访问系统**
   - 系统首页：http://127.0.0.1:8000
   - API文档：http://127.0.0.1:8000/docs

### 数据准备（可选）

如需使用处理好的数据集进行模型训练：

```bash
# 从原始SORDI数据集准备数据（需提供archive.zip）
python scripts/prepare_dataset.py
```

数据集将处理为YOLO格式，保存在`data/processed/`目录下。

## 项目结构

```
smart-warehouse-system/
├── run.py                          # 系统启动入口
├── requirements.txt                # Python依赖清单
├── README.md                       # 项目说明
├── backend/                        # 后端代码
│   ├── app.py                      # FastAPI主应用
│   ├── config.py                   # 系统配置
│   ├── database.py                 # 数据库连接
│   ├── models.py                   # 数据模型
│   ├── schemas.py                  # Pydantic模式
│   ├── api/                        # API路由
│   │   ├── detection.py            # 检测API
│   │   ├── inventory.py            # 库存API
│   │   ├── sensor.py               # 传感器API
│   │   └── stats.py                # 统计API
│   └── algorithms/                 # 算法模块
│       ├── object_detection.py     # 目标检测算法
│       ├── sensor_fusion.py        # 多传感器融合算法
│       └── anomaly_detection.py    # 异常检测算法
├── frontend/                       # 前端代码
│   ├── index.html                  # 主页面
│   ├── css/style.css               # 样式文件
│   └── js/                         # JavaScript模块
│       ├── app.js                  # 主应用逻辑
│       ├── dashboard.js            # 仪表盘
│       ├── detection.js            # 检测页面
│       ├── inventory.js            # 库存管理
│       ├── sensor.js               # 传感器数据
│       ├── records.js              # 检测记录
│       └── settings.js             # 系统设置
├── data/                           # 数据目录
│   ├── processed/                  # 处理后数据集（YOLO格式）
│   ├── uploads/                    # 用户上传图像
│   └── database/warehouse.db       # SQLite数据库
├── models/                         # 模型文件（可选）
├── scripts/                        # 工具脚本
│   ├── prepare_dataset.py          # 数据准备脚本
│   ├── init_db.py                  # 数据库初始化
│   └── test_detection.py           # 检测功能测试
├── tests/                          # 自动化测试
│   ├── test_algorithms.py          # 算法单元测试
│   ├── test_api.py                 # API集成测试
│   └── test_database.py            # 数据库测试
├── docs/                           # 文档
│   ├── 需求规格说明书.md
│   └── 设计报告.md
└── prompt/                         # AI对话日志
```

## API接口

系统提供完整的RESTful API，主要接口如下：

### 检测接口
- `POST /api/detection/upload` - 上传图像并执行完整检测
- `GET /api/detection/records` - 获取检测记录列表
- `PUT /api/detection/records/{id}/sort` - 更新分拣状态

### 库存接口
- `GET /api/inventory` - 获取库存列表
- `POST /api/inventory` - 新增库存项
- `POST /api/inventory/{id}/inbound` - 入库操作
- `POST /api/inventory/{id}/outbound` - 出库操作

### 传感器接口
- `GET /api/sensor` - 获取传感器数据
- `POST /api/sensor` - 上报传感器数据
- `GET /api/sensor/stats` - 传感器统计

### 统计接口
- `GET /api/stats/dashboard` - 仪表盘综合统计
- `GET /api/stats/trend` - 检测趋势
- `GET /api/stats/classes` - 类别信息
- `GET /api/stats/system` - 系统信息

完整API文档请访问：http://127.0.0.1:8000/docs

## 检测类别

系统支持以下6类仓储物料的识别：

| 类别ID | 英文名称 | 中文名称 | 说明 |
|--------|----------|----------|------|
| 0 | cardboard_box | 纸箱 | 快递盒、包装盒 |
| 1 | pallet | 托盘 | 仓储托盘 |
| 2 | stillage | 料架 | 笼车、物料架 |
| 3 | forklift | 叉车 | 搬运叉车 |
| 4 | eps_box | 泡沫箱 | 泡沫包装盒 |
| 5 | wheelie_bin | 滚轮料箱 | 滚轮料箱 |

## 数据集

本项目使用SORDI（Smart Object Recognition Dataset for Industry）工业数据集：

- 原始数据：46,268张标注图像（DR-1 + DR-2）
- 选择子集：6类仓储物料，每类400张，去重后共2,333张
- 训练集：1,633张（70%）
- 验证集：466张（20%）
- 测试集：234张（10%）
- 标注格式：JSON → YOLO格式转换

## 测试

运行自动化测试：

```bash
pip install pytest httpx
pytest tests/ -v
```

测试覆盖：
- 算法单元测试：17个用例
- API集成测试：18个用例
- 数据库测试：8个用例
- **总计：43个测试用例，全部通过**

## 功能演示流程

1. **启动系统**：运行`python run.py`，访问http://127.0.0.1:8000
2. **查看仪表盘**：系统概览、统计数据、趋势图表
3. **物料检测**：
   - 进入"物料检测"页面
   - 上传一张仓储物料图像（可使用`data/processed/`中的图片）
   - 点击"开始检测"
   - 查看检测结果（目标类别、置信度）、融合结果（通过/警告/拒绝）、异常检测结果
4. **库存管理**：查看库存、执行入库/出库操作
5. **传感器数据**：查看传感器历史数据和统计
6. **检测记录**：查看历史检测记录，更新分拣状态
7. **系统设置**：查看系统信息，配置参数

## 文档

- [需求规格说明书](docs/需求规格说明书.md)
- [设计报告](docs/设计报告.md)

## AI使用说明

本项目开发过程中使用了AI编程工具辅助开发，具体使用情况详见设计报告第6章"AI使用披露"。

所有AI生成的代码均经过人工审查、理解和优化，确保功能正确、代码规范。

## 许可证

本项目为课程设计项目，仅供学习和研究使用。

## 联系方式

- 学生姓名：孙士凯
- 学号：17
- 课程：制造智能技术课程设计
