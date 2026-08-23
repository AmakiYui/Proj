@echo off
REM ============================================================
REM boot.bat -- Windows 批处理引导程序 (Q4 Day2 升级版)
REM 一个入口走所有 server:python -m src.server.cli <style>
REM ============================================================

REM UTF-8 控制台 + Python 编码
chcp 65001 > nul
set PYTHONIOENCODING=utf-8

REM 切到脚本所在目录
cd /d "%~dp0"

:MENU
echo ============================================================
echo   Proj 启动菜单 (Q4 Day2)
echo ============================================================
echo   [1] 命令行版 (main.py)        -- while True input/print
echo   [2] 网络 server (cli.py)     -- 选 style 跑服务端
echo   [3] 客户端 (client.py)       -- 测服务端是否活着
echo   [0] 退出
echo ============================================================
set /p CHOICE=请选择 [0-3]:

if "%CHOICE%"=="1" goto CMD
if "%CHOICE%"=="2" goto CLI
if "%CHOICE%"=="3" goto CLI
if "%CHOICE%"=="0" goto END
echo [boot.bat] 输入有误,请重试
echo.
goto MENU

:CMD
echo [boot.bat] 启动命令行版 main.py ...
python boot.py
goto DONE

:CLI
echo ============================================================
echo   server 风格选择
echo ============================================================
echo   [1] simple -- 串行 socket
echo   [2] thread -- 手搓多线程
echo   [3] pool   -- ThreadingMixIn
echo   [4] pro    -- 终极版(PID+日志+var/)
echo ============================================================
set /p STYLE=请选择风格 [1-4]:
if "%STYLE%"=="1" set NAME=simple
if "%STYLE%"=="2" set NAME=thread
if "%STYLE%"=="3" set NAME=pool
if "%STYLE%"=="4" set NAME=pro
if "%NAME%"=="" (
    echo [boot.bat] 输入有误,返回主菜单
    goto MENU
)
echo [boot.bat] python -m src.proj.cli %NAME%
python -m src.proj.cli %NAME%
goto DONE

:DONE
if errorlevel 1 (
    echo.
    echo [boot.bat] 程序退出码非 0
    pause
)
goto MENU

:END
echo [boot.bat] 再见!
exit /b 0