@echo off
echo ================================
echo TypeSage Docker 部署脚本
echo ================================

echo 1. 检查Docker状态...
docker --version
if %errorlevel% neq 0 (
    echo 错误: Docker未安装或未启动
    pause
    exit /b 1
)

echo 2. 停止已有容器...
docker-compose down

echo 3. 清理旧镜像（可选）...
set /p cleanup="是否清理旧镜像? (y/n): "
if /i "%cleanup%"=="y" (
    docker system prune -f
    docker image prune -f
)

echo 4. 构建并启动服务...
docker-compose up --build -d

echo 5. 检查服务状态...
timeout /t 10
docker-compose ps

echo 6. 显示日志...
echo 后端日志:
docker-compose logs backend --tail=20
echo 前端日志:
docker-compose logs frontend --tail=20

echo ================================
echo 部署完成!
echo 访问地址: http://localhost
echo 后端API: http://localhost:8000
echo ================================

echo 按任意键继续监控日志...
pause
docker-compose logs -f 