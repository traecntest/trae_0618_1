# 测试应用

测试生成的应用

## 版本信息
- 版本: 1.0.0
- 生成时间: 2026-06-18 09:53:45.827135

## 功能特性
- 表单数量: 1 个
- 工作流数量: 1 个
- 数据模型数量: 1 个
- 页面数量: 0 个

## 快速开始

### 方式一: Docker 部署

```bash
docker build -t 测试应用 .
docker run -p 8000:8000 测试应用
```

### 方式二: 本地运行

#### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 前端
```bash
cd frontend
npm install
npm run serve
```

## API 文档

启动后访问: http://localhost:8000/docs
