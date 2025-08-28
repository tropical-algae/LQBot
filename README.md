<div align="center">
  <img src="asset/image/logo.png" style="height:4em; vertical-align:middle;">
  <h2>基于napcat开发的QQ聊天机器人</h2>
</div>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Language-English-blue.svg"></a>
  <a href="README_CN.md"><img src="https://img.shields.io/badge/Language-简体中文-red.svg"></a>
  <a href="README_CN.md"><img src="https://img.shields.io/badge/Document-参考文档-green.svg"></a>
</p>

# LQBot

LQBot是一个由agent驱动的QQ机器人助手。

关于为什么取名LQBot已经忘记了，莫名其妙的名字。不过这个不重要，目前agent已添加诸多工具，在聊天过程中使用他们

🔨 **已支持的功能**：

- 查询github每日趋势
- 查看超级地球日志与战况
- 语音回复
- 查看实时天气与天气预报
- 清除记忆
- 设定提醒事项与第三方信息推送（开发中）
- 指令控制（开发中）
- 以及其他我未来想到并有空开发的功能（饼）

🔐 **权限控制**：

此外，诸多配置支持你对功能权限进行细微的控制，具体使用方法请参考部署文档

| 配置项              | 方法            | 状态         |
| ------------------- | --------------- | ------------ |
| 群组对Bot使用权限   | 黑名单 / 白名单 | ✅           |
| Bot对命令使用权限   | 配置 + 黑名单   | ✅           |
| Agent对工具使用权限 | bool开关        | ✅（未完善） |

______________________________________________________________________

## 🚀 部署方法

本项目支持Docker镜像部署（目前因重构仍需调整，暂未实现完整CI/CD流程），**推荐使用Docker进行部署**。

鸽

______________________________________________________________________

## 🛠 开发指南

### 环境依赖

- Ubuntu 22.04 / 24.04
- Python 3.10+
- Poetry (Python Package Manager)
- Make

### 如何开始？

1. 运行以下命令安装poetry与依赖库

```shell
make install
```

2. 配置 `.env` 环境变量，在 [config](src/lqbot/utils/config.py) 中得到参考

1. 项目开发，运行以下命令启动系统

```shell
poe run
```

4. 代码检测与静态分析

```shell
poe check        # 静态检测与代码分析
poe test         # 代码测试
poe check-test   # 静态检测与代码分析 + 代码测试
poe clean        # 清理cache
```

______________________________________________________________________

## ✨ 后期规划

接入MCP（鸽
