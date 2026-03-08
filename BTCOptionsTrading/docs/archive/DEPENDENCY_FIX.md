# 依赖问题修复指南

## 问题：numpy==1.21.6 安装失败

这个错误通常是因为：
1. Python 版本太新（如 Python 3.11+），numpy 1.21.6 不支持
2. Python 版本太旧（如 Python 3.7），某些依赖不兼容
3. 系统缺少编译工具

## 解决方案

### 方案 1：使用自动修复脚本（推荐）

```bash
cd backend
./fix_dependencies.sh
```

脚本会：
- 检查 Python 版本
- 提供三种安装选项
- 自动处理依赖冲突
- 验证安装结果

### 方案 2：使用最小化依赖

```bash
cd backend
pip install -r requirements-minimal.txt
```

这个文件只包含运行时必需的核心依赖，版本要求更宽松。

### 方案 3：手动安装核心依赖

```bash
cd backend

# 升级 pip
pip install --upgrade pip

# 安装核心依赖（不指定具体版本）
pip install fastapi uvicorn pydantic websockets
pip install numpy pandas
pip install aiohttp requests
pip install python-dotenv structlog
pip install "sqlalchemy<2.0.0"
pip install apscheduler pyyaml
```

### 方案 4：使用虚拟环境（推荐用于生产）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements-minimal.txt
```

### 方案 5：针对特定 Python 版本

#### Python 3.11+
```bash
# numpy 需要更新版本
pip install "numpy>=1.23.0"
pip install -r requirements-minimal.txt
```

#### Python 3.7-3.8
```bash
# 使用旧版本
pip install "numpy>=1.19.0,<1.22.0"
pip install -r requirements-minimal.txt
```

## 检查 Python 版本

```bash
python3 --version
```

推荐版本：Python 3.8 - 3.10

## 常见错误及解决方法

### 错误 1: "No matching distribution found"

**原因**: 包版本与 Python 版本不兼容

**解决**:
```bash
# 不指定版本，让 pip 自动选择兼容版本
pip install numpy pandas scipy
```

### 错误 2: "Failed building wheel"

**原因**: 缺少编译工具

**解决**:

Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install python3-dev build-essential
```

CentOS/RHEL:
```bash
sudo yum install python3-devel gcc gcc-c++
```

macOS:
```bash
xcode-select --install
```

### 错误 3: "Permission denied"

**原因**: 权限不足

**解决**:
```bash
# 使用 --user 标志
pip install --user -r requirements-minimal.txt

# 或使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt
```

### 错误 4: "SSL Certificate Error"

**原因**: SSL 证书问题

**解决**:
```bash
# 临时解决（不推荐用于生产）
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements-minimal.txt

# 或更新证书
pip install --upgrade certifi
```

## 验证安装

安装完成后，验证关键包：

```bash
python3 << EOF
import fastapi
import uvicorn
import numpy
import pandas
import sqlalchemy
import aiohttp
print("所有关键包导入成功！")
EOF
```

## 测试运行

```bash
cd backend
python run_api.py
```

如果看到 "Uvicorn running on http://0.0.0.0:8000"，说明安装成功。

## 仍然有问题？

### 1. 查看详细错误

```bash
pip install -r requirements.txt -v
```

### 2. 清除缓存

```bash
pip cache purge
pip install -r requirements-minimal.txt
```

### 3. 使用 conda（如果可用）

```bash
conda create -n btc-trading python=3.9
conda activate btc-trading
pip install -r requirements-minimal.txt
```

### 4. 检查系统资源

```bash
# 检查磁盘空间
df -h

# 检查内存
free -h
```

## 更新依赖文件

如果你想更新 requirements.txt：

```bash
# 生成当前环境的依赖
pip freeze > requirements-current.txt

# 只保留直接依赖
pip install pipreqs
pipreqs . --force
```

## 生产环境建议

1. **使用虚拟环境**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **锁定依赖版本**
   ```bash
   pip freeze > requirements-lock.txt
   ```

3. **定期更新**
   ```bash
   pip list --outdated
   pip install --upgrade package_name
   ```

4. **使用 Docker**（最佳实践）
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements-minimal.txt .
   RUN pip install -r requirements-minimal.txt
   COPY . .
   CMD ["python", "run_api.py"]
   ```

## 联系支持

如果以上方法都无法解决问题，请提供：
1. Python 版本 (`python3 --version`)
2. 操作系统信息 (`uname -a`)
3. 完整错误信息
4. pip 版本 (`pip --version`)
