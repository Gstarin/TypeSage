# TypeSage Docker 容器化部署指南

## 🐳 Windows 开发环境准备

### 1. 安装 Docker Desktop
1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. 安装并启动 Docker Desktop
3. 确保 WSL2 已启用（推荐）

### 2. 验证安装
```powershell
docker --version
docker-compose --version
```

## 🚀 本地测试部署

### 快速启动
```powershell
# 运行部署脚本
.\deploy.bat
```

### 手动部署步骤
```powershell
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 访问应用
- **前端**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## ☁️ 云服务器部署

### 方案一：直接部署到云服务器

#### 1. 购买云服务器
推荐配置：
- **CPU**: 2核
- **内存**: 4GB
- **存储**: 40GB SSD
- **操作系统**: Ubuntu 20.04/22.04

#### 2. 服务器环境准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo apt install docker-compose -y

# 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker-compose --version
```

#### 3. 上传项目代码
```powershell
# 方式1: 使用Git
git clone https://github.com/your-username/TypeSage.git
cd TypeSage

# 方式2: 使用SCP上传
scp -r C:\Users\86159\Desktop\TypeSage user@server-ip:/home/user/
```

#### 4. 生产环境配置
```bash
# 创建生产环境配置
cp docker-compose.yml docker-compose.prod.yml

# 编辑生产配置
nano docker-compose.prod.yml
```

生产环境配置示例：
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: typesage-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./database/typesage.db
      - CORS_ORIGINS=https://your-domain.com,http://your-ip
    volumes:
      - ./backend/database:/app/database
    networks:
      - typesage-network
    restart: always

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: typesage-frontend
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    networks:
      - typesage-network
    restart: always

networks:
  typesage-network:
    driver: bridge
```

#### 5. 启动生产服务
```bash
# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 方案二：使用云服务商容器服务

#### 阿里云容器实例 ACI
1. 上传镜像到阿里云容器镜像服务
2. 创建容器实例
3. 配置负载均衡

#### 腾讯云容器服务 TKE
1. 创建集群
2. 部署工作负载
3. 配置服务访问

## 🔧 配置优化

### 1. 环境变量配置
创建 `.env` 文件：
```env
# 数据库配置
DATABASE_URL=sqlite:///./database/typesage.db

# CORS配置
CORS_ORIGINS=https://your-domain.com,http://localhost

# 其他配置
DEBUG=false
LOG_LEVEL=INFO
```

### 2. 域名和SSL配置
```bash
# 安装Nginx和Certbot
sudo apt install nginx certbot python3-certbot-nginx -y

# 配置域名
sudo nano /etc/nginx/sites-available/typesage

# 申请SSL证书
sudo certbot --nginx -d your-domain.com
```

### 3. 数据库备份
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker cp typesage-backend:/app/database/typesage.db ./backup/typesage_$DATE.db
EOF

chmod +x backup.sh

# 设置定时备份
crontab -e
# 添加: 0 2 * * * /path/to/backup.sh
```

## 📊 监控和维护

### 1. 容器监控
```bash
# 查看资源使用
docker stats

# 查看容器日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart backend
docker-compose restart frontend
```

### 2. 更新部署
```bash
# 拉取最新代码
git pull origin main

# 重新构建并部署
docker-compose down
docker-compose up --build -d
```

### 3. 故障排查
```bash
# 进入容器调试
docker exec -it typesage-backend bash
docker exec -it typesage-frontend sh

# 查看详细日志
docker-compose logs --details backend
```

## 🚨 安全建议

1. **防火墙配置**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

2. **定期更新**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 更新Docker镜像
   docker-compose pull
   docker-compose up -d
   ```

3. **数据备份**
   - 定期备份数据库文件
   - 备份配置文件
   - 使用云存储备份

## 🆘 常见问题

### Q: 容器启动失败
```bash
# 查看详细错误
docker-compose logs backend
docker-compose logs frontend

# 检查端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :8000
```

### Q: 前端无法访问后端
1. 检查网络配置
2. 确认CORS设置
3. 查看防火墙规则

### Q: 数据库文件权限问题
```bash
# 修复权限
sudo chown -R 1000:1000 backend/database/
```

## 📞 技术支持

如遇问题，请提供以下信息：
- 错误日志: `docker-compose logs`
- 系统信息: `docker version`, `docker-compose version`
- 容器状态: `docker-compose ps` 