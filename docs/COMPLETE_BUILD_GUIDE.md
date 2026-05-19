# UAV 气象驱动无人机 VRP 智能路径规划系统 —— 零基础完整构建指南

> **适用人群**：零编程基础、无任何开发经验的初学者  
> **最终目标**：跟着本指南，从一台空白电脑开始，独立完成整套项目的环境搭建、源码运行、调试测试、Docker 容器化部署，直至线上发布运维  
> **预计总耗时**：首次完整走完约 8~16 小时（含软件下载安装时间）  
> **文档版本**：v1.0  
> **最后更新**：2026-05-14  

---

## 导读：这份指南能帮你做什么？

你是否遇到过这样的情况：拿到一个看起来很厉害的项目源码，但完全不知道从哪里下手？环境搭不起来、代码跑不通、报错看不懂？

本指南就是为解决这个问题而生。我们会像拼积木一样，一步步把整个项目从零搭建起来。

**读完这份指南，你将能够：**

| 能力 | 说明 |
|------|------|
| 搭建完整开发环境 | 在 Windows/Mac/Linux 上安装所有必需的工具软件 |
| 拉取并理解项目源码 | 从 GitHub 获取代码，搞清楚每个文件夹是干什么的 |
| 独立开发各模块 | 修改后端接口、前端页面、移动端功能 |
| 本地联调测试 | 让前端、后端、数据库、缓存等所有服务在本地跑通 |
| 容器化部署上线 | 用 Docker 一键打包发布到服务器 |
| 日常运维排障 | 处理常见的报错、重启、配置修改等问题 |

---

## 目录

- [第一章：环境搭建 —— 把工具都装好](#第一章环境搭建--把工具都装好)
  - [1.1 开发环境选型标准与版本适配](#11-开发环境选型标准与版本适配)
  - [1.2 JDK 17 安装与配置](#12-jdk-17-安装与配置)
  - [1.3 Maven 安装配置与镜像源设置](#13-maven-安装配置与镜像源设置)
  - [1.4 Node.js 与 npm 安装配置](#14-nodejs-与-npm-安装配置)
  - [1.5 Docker 与 Docker Compose 安装](#15-docker-与-docker-compose-安装)
  - [1.6 Flutter SDK 安装与配置](#16-flutter-sdk-安装与配置)
  - [1.7 Python 环境配置](#17-python-环境配置)
  - [1.8 IDE 开发工具安装与配置](#18-ide-开发工具安装与配置)
  - [1.9 Git 安装与配置](#19-git-安装与配置)
  - [1.10 中间件安装（MySQL / Redis / Nacos / Kafka）](#110-中间件安装mysql--redis--nacos--kafka)
- [第二章：源码获取 —— 把代码拿下来](#第二章源码获取--把代码拿下来)
  - [2.1 项目拉取](#21-项目拉取)
  - [2.2 项目目录结构详解](#22-项目目录结构详解)
  - [2.3 各模块职责说明](#23-各模块职责说明)
- [第三章：模块开发 —— 开始写代码](#第三章模块开发--开始写代码)
  - [3.1 Java 17 必备基础知识点](#31-java-17-必备基础知识点)
  - [3.2 SpringBoot 微服务核心架构原理](#32-springboot-微服务核心架构原理)
  - [3.3 Maven 依赖管理与多模块配置详解](#33-maven-依赖管理与多模块配置详解)
  - [3.4 后端微服务模块开发实战](#34-后端微服务模块开发实战)
  - [3.5 数据库设计与连接配置](#35-数据库设计与连接配置)
  - [3.6 Nacos 服务注册与配置中心接入](#36-nacos-服务注册与配置中心接入)
  - [3.7 Redis 缓存与 Kafka 消息队列使用](#37-redis-缓存与-kafka-消息队列使用)
  - [3.8 Vue 前端项目开发指南](#38-vue-前端项目开发指南)
  - [3.9 Flutter 移动端开发指南](#39-flutter-移动端开发指南)
- [第四章：联调测试 —— 让所有部分一起工作](#第四章联调测试--让所有部分一起工作)
  - [4.1 后端微服务本地联调](#41-后端微服务本地联调)
  - [4.2 前后端接口联调](#42-前后端接口联调)
  - [4.3 Flutter 客户端联调](#43-flutter-客户端联调)
  - [4.4 功能测试思路与测试用例设计](#44-功能测试思路与测试用例设计)
  - [4.5 接口测试执行方案](#45-接口测试执行方案)
- [第五章：容器部署 —— 打包发布上线](#第五章容器部署--打包发布上线)
  - [5.1 Docker 镜像构建与多阶段打包](#51-docker-镜像构建与多阶段打包)
  - [5.2 Docker Compose 服务编排](#52-docker-compose-服务编排)
  - [5.3 一键部署完整流程](#53-一键部署完整流程)
  - [5.4 生产环境服务器准备与域名配置](#54-生产环境服务器准备与域名配置)
- [第六章：运维排障 —— 出了问题怎么办](#第六章运维排障--出了问题怎么办)
  - [6.1 日常维护清单](#61-日常维护清单)
  - [6.2 常见报错原因分析与解决方案](#62-常见报错原因分析与解决方案)
- [附录：专题文档索引](#附录专题文档索引)

---

## 第一章：环境搭建 —— 把工具都装好

### 1.0 开始之前：几个重要概念

在动手安装之前，先了解几个会反复出现的名词，不用死记，用到时回来查就行：

| 名词 | 通俗解释 | 在本项目中的作用 |
|------|----------|-----------------|
| **JDK（Java 开发工具包）** | 运行和编译 Java 代码必需的工具集 | 后端所有微服务都用 Java 17 编写 |
| **Maven** | Java 项目的"管家"，负责下载依赖库、编译打包 | 统一管理 10+ 个微服务模块的依赖和构建 |
| **npm（Node 包管理器）** | Node.js 的"管家"，下载前端项目需要的各种库 | 管理 Vue 前端项目依赖 |
| **Docker** | 把应用和环境打包成"集装箱"，到哪都能跑 | 让所有服务在生产环境一键启动 |
| **微服务** | 把一个大系统拆成多个小服务，各管各的事 | 本项目拆成 10 个独立服务 |
| **Nacos** | 服务"通讯录"+"配置中心" | 让微服务之间能找到彼此，统一管理配置 |
| **中间件** | 通用的基础软件，像"积木块"一样被各服务调用 | MySQL（存数据）、Redis（缓存）、Kafka（消息传递） |

### 1.1 开发环境选型标准与版本适配

#### 操作系统选择

本项目支持三大主流操作系统。对于零基础用户，**强烈推荐 Windows 10/11**：

| 操作系统 | 推荐指数 | 说明 |
|----------|:-------:|------|
| **Windows 10/11** |   | 软件安装最简单，有图形化安装向导 |
| **macOS** |   | 开发体验好，但部分工具安装方式不同 |
| **Linux (Ubuntu 22.04+)** |   | 服务器首选，但新手门槛较高 |

#### 完整版本适配表

**这是本项目所有工具的精确版本号。请严格按此表安装，版本不对可能导致各种奇怪的报错：**

| 工具/框架 | 必须版本 | 用途 | 强制匹配？ |
|-----------|:--------:|------|:---------:|
| **JDK（Java 开发工具包）** | **17** | 编译运行所有后端微服务 | ✅ 必须是 17 |
| **Maven** | 3.8+ | 项目构建和依赖管理 | ✅ 3.6 以下不行 |
| **Node.js** | 18.x LTS | 运行 Vue 前端开发服务器 | ✅ 推荐 LTS |
| **npm** | 9.x（随 Node 自带） | 前端包管理 | 随 Node 自动安装 |
| **Python** | 3.8 ~ 3.11 | WRF 数据处理、数据同化算法 | ✅ 3.12 可能有兼容问题 |
| **Docker Engine** | 24.0+ | 容器化运行所有服务 | 建议最新稳定版 |
| **Docker Compose** | v2.20+ | 编排多容器服务 | ✅ v1 已淘汰 |
| **Flutter SDK** | 3.2.0 ~ 3.x | 移动端跨平台应用开发 | ✅ 稳定版 |
| **Dart SDK** | 3.2.0+（随 Flutter 自带） | Flutter 开发语言 | 随 Flutter 自动安装 |
| **Git** | 2.40+ | 源码版本管理 | 建议最新版 |
| **MySQL** | 8.0 | 主数据库，存储所有业务数据 | ✅ 5.x 不兼容 |
| **Redis** | 6.2 | 缓存数据库，加速数据读取 | 7.x 也可以 |
| **Nacos** | 2.3.0 | 服务注册发现 + 配置中心 | ✅ 必须 2.x |
| **Kafka** | 3.6+ | 消息队列，微服务间异步通信 | 3.x 系列都可以 |
| **CMake** | 3.10+ | C++ 边缘 SDK 编译 | 仅边缘端需要 |

> **关于"强制匹配"的说明**：标记为 ✅ 的项，如果版本不匹配，项目可能会编译报错、启动失败或出现运行时异常。尤其是 JDK 17 和 MySQL 8.0，这两个是最常见的新手踩坑点。

#### 安装顺序建议

按以下顺序安装，可以避免依赖缺失导致的安装失败：

```
1. Git          →  拉取源码
2. JDK 17       →  Java 开发基础
3. Maven        →  需要先装 JDK
4. Node.js      →  独立安装，不依赖其他
5. Python       →  独立安装，不依赖其他
6. Docker       →  独立安装，不依赖其他
7. Flutter      →  独立安装，不依赖其他
8. IDE (IDEA/VS Code) → 最后装，配置时用到前面的工具路径
```

---

### 1.2 JDK 17 安装与配置

#### 第一步：下载 JDK 17

JDK（Java Development Kit，Java 开发工具包）是运行所有 Java 程序的基础环境。我们使用 **Eclipse Temurin（原 AdoptOpenJDK）** 发行版，因为它免费、稳定、受广泛支持。

1. 打开浏览器，访问：https://adoptium.net/download/
2. 在页面上选择：
   - **操作系统**：按你的系统选 Windows / macOS / Linux
   - **架构**：一般选 x64（绝大多数电脑都是 64 位）
   - **版本**：**Java 17 (LTS)**
   - **JVM**：HotSpot（默认推荐）
3. 点击下载 `.msi`（Windows）或 `.pkg`（macOS）安装包

#### 第二步：安装 JDK 17

**Windows 用户：**

1. 双击下载的 `.msi` 文件
2. 一路点击 "Next"（下一步），**特别注意这一页**：
   - 勾选 **"Set JAVA_HOME variable"**（设置 JAVA_HOME 环境变量）
   - 这个选项会把 JDK 安装路径自动配置到系统中
3. 点击 "Install" 完成安装

**macOS 用户：**

1. 双击 `.pkg` 文件，按向导完成安装
2. 安装完成后，JDK 通常位于：`/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home`

**Linux (Ubuntu) 用户：**

```bash
# 添加 Adoptium 仓库
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo apt-key add -
sudo add-apt-repository --yes https://packages.adoptium.net/artifactory/deb
sudo apt-get update

# 安装 JDK 17
sudo apt-get install temurin-17-jdk
```

#### 第三步：验证安装

打开 **终端/命令行**（Windows 按 `Win+R`，输入 `cmd` 回车；macOS 打开 "终端" 应用），输入：

```bash
java -version
```

如果看到类似以下输出，说明安装成功：

```
openjdk version "17.0.9" 2023-10-17
OpenJDK Runtime Environment Temurin-17.0.9+9 (build 17.0.9+9)
OpenJDK 64-Bit Server VM Temurin-17.0.9+9 (build 17.0.9+9, mixed mode, sharing)
```

> **关键检查**：确认第一行显示的是 `"17.x.x"`，如果不是 17，说明你电脑上可能之前安装了其他版本，需要调整 JAVA_HOME 环境变量。

#### 第四步：确认 JAVA_HOME 环境变量

```bash
# Windows CMD
echo %JAVA_HOME%

# macOS / Linux
echo $JAVA_HOME
```

应该输出类似 `C:\Program Files\Eclipse Adoptium\jdk-17.0.9.9-hotspot\` 的路径。

如果为空，请手动设置：

**Windows：**
1. 右键 "此电脑" → "属性" → "高级系统设置" → "环境变量"
2. 在 "系统变量" 中新建：
   - 变量名：`JAVA_HOME`
   - 变量值：你的 JDK 安装路径（例如 `C:\Program Files\Eclipse Adoptium\jdk-17.0.9.9-hotspot\`）
3. 找到 `Path` 变量，新建一条：`%JAVA_HOME%\bin`

**macOS / Linux：**

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home
export PATH=$JAVA_HOME/bin:$PATH

# 生效
source ~/.bashrc  # 或 source ~/.zshrc
```

---

### 1.3 Maven 安装配置与镜像源设置

#### 什么是 Maven？为什么需要它？

如果把写 Java 代码比作做菜，Maven 就是帮你买菜、洗菜、切菜的助手。Java 项目通常会用到几十甚至上百个第三方库（叫做"依赖"），手动管理这些库的下载和版本极其麻烦。Maven 自动帮你完成这一切。

#### 第一步：下载 Maven

1. 打开：https://maven.apache.org/download.cgi
2. 下载 **Binary zip archive**（Windows/macOS/Linux 通用）
3. 解压到你喜欢的目录，例如：
   - Windows：`C:\tools\apache-maven-3.9.6`
   - macOS/Linux：`/usr/local/apache-maven-3.9.6`

> **小技巧**：不要把 Maven 解压到中文路径或带空格的路径（如 `C:\Program Files\`），这可能导致奇怪的报错。

#### 第二步：配置环境变量

**Windows：**
1. 在 "环境变量" 中新建：
   - 变量名：`MAVEN_HOME`
   - 变量值：`C:\tools\apache-maven-3.9.6`（改成你的实际路径）
2. 在 `Path` 变量中新建：`%MAVEN_HOME%\bin`

**macOS / Linux：**

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加
export MAVEN_HOME=/usr/local/apache-maven-3.9.6
export PATH=$MAVEN_HOME/bin:$PATH

source ~/.bashrc
```

#### 第三步：验证安装

重新打开终端，输入：

```bash
mvn -version
```

期望输出中包含：

```
Apache Maven 3.9.x
Java version: 17.0.x
```

> **注意**：确保显示的 Java version 是 17！如果不是，回到上一节检查 JAVA_HOME。

#### 第四步：配置国内镜像源（重要！）

Maven 默认从国外的中央仓库下载依赖，在国内速度很慢甚至超时。我们需要配置 **阿里云镜像源**。

找到 Maven 的配置文件：
- `%MAVEN_HOME%\conf\settings.xml`（全局配置）
- 或 `C:\Users\你的用户名\.m2\settings.xml`（用户配置，推荐）

编辑 `settings.xml`，在 `<mirrors>` 标签内添加：

```xml
<mirror>
  <id>aliyunmaven</id>
  <mirrorOf>central</mirrorOf>
  <name>阿里云公共仓库</name>
  <url>https://maven.aliyun.com/repository/public</url>
</mirror>
```

> **如果文件不存在**，在 `C:\Users\你的用户名\.m2\` 目录下新建 `settings.xml`，复制以下完整内容：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
          http://maven.apache.org/xsd/settings-1.0.0.xsd">
  <mirrors>
    <!-- 阿里云 Maven 镜像 -->
    <mirror>
      <id>aliyunmaven</id>
      <mirrorOf>central</mirrorOf>
      <name>阿里云公共仓库</name>
      <url>https://maven.aliyun.com/repository/public</url>
    </mirror>
    <!-- Spring 插件镜像 -->
    <mirror>
      <id>aliyunspring</id>
      <mirrorOf>spring-milestones,spring-snapshots</mirrorOf>
      <name>阿里云 Spring 仓库</name>
      <url>https://maven.aliyun.com/repository/spring</url>
    </mirror>
  </mirrors>
</settings>
```

> 更多 Maven 详细教程请参阅：[MAVEN_FIX.md](./MAVEN_FIX.md)

---

### 1.4 Node.js 与 npm 安装配置

#### 什么是 Node.js 和 npm？

- **Node.js**：让 JavaScript 可以在浏览器之外运行的平台。我们的 Vue 前端开发服务器需要它。
- **npm（Node Package Manager）**：Node 的包管理器，相当于 Java 的 Maven。前端项目用它来下载 Vue、各种 UI 组件等依赖。

#### 第一步：下载安装 Node.js

1. 访问 Node.js 官网：https://nodejs.org/
2. 下载 **LTS（长期支持版）**，目前推荐 v18.x
   - LTS 版本最稳定，bug 最少
3. 双击安装包，一路 "Next" 完成安装

#### 第二步：验证安装

```bash
node -v
# 应输出：v18.x.x

npm -v
# 应输出：9.x.x
```

#### 第三步：配置 npm 国内镜像源

和 Maven 一样，npm 默认源在国外，需要切换到国内镜像：

```bash
# 设置淘宝镜像源（国内最快）
npm config set registry https://registry.npmmirror.com

# 验证是否设置成功
npm config get registry
# 应输出：https://registry.npmmirror.com/
```

#### 第四步：npm 常用命令速查

| 命令 | 作用 | 在项目中的使用场景 |
|------|------|-------------------|
| `npm install` | 安装 package.json 中声明的所有依赖 | 第一次拉取前端项目后执行 |
| `npm install 包名` | 安装某个指定的包 | 新增功能需要新依赖时 |
| `npm run dev` | 启动开发服务器 | 本地开发时运行前端 |
| `npm run build` | 构建生产版本 | 部署前打包前端资源 |
| `npm update` | 更新依赖包 | 版本升级时 |

---

### 1.5 Docker 与 Docker Compose 安装

#### 什么是 Docker？（用一个比喻理解）

想象你要搬家：把所有家具、电器、日用品打包进一个标准集装箱，然后这个集装箱不管搬到哪个城市，都能直接使用。Docker 就是这个"集装箱"：

- **镜像（Image）**：集装箱的设计图纸
- **容器（Container）**：根据图纸造出来的正在运行的集装箱
- **Docker Compose**：一次性编排多个集装箱（容器）如何协作

在本项目中，Docker 让我们可以一条命令就把 MySQL、Redis、Nacos、Kafka 和所有微服务全部启动。

#### 第一步：安装 Docker Desktop

**Windows：**

1. 访问：https://www.docker.com/products/docker-desktop/
2. 下载 Docker Desktop for Windows
3. 双击安装，一路下一步
4. 安装完成后**重启电脑**（这一步很重要！）
5. 重启后 Docker Desktop 会自动启动（任务栏右下角会出现鲸鱼图标）

> **Windows 特别说明**：
> - Docker Desktop 需要启用虚拟化技术（VT-x/AMD-V），一般新电脑默认已开启
> - 如果安装失败提示虚拟化未开启，需要进 BIOS 打开（不同品牌电脑进入 BIOS 的按键不同，常见的是开机按 F2 / F10 / Del）
> - Docker Desktop 需要 WSL2（Windows Subsystem for Linux 2），安装程序会自动处理

**macOS：**

1. 访问：https://www.docker.com/products/docker-desktop/
2. 下载对应的芯片版本（Intel 芯片选 Intel，M1/M2/M3 芯片选 Apple Silicon）
3. 将 Docker.app 拖入 Applications 文件夹
4. 首次启动需要授权系统权限

**Linux (Ubuntu)：**

```bash
# 使用官方安装脚本（推荐）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户加入 docker 组（避免每次加 sudo）
sudo usermod -aG docker $USER
# 重新登录后生效
```

#### 第二步：验证安装

```bash
docker --version
# Docker version 24.x.x

docker-compose --version
# Docker Compose version v2.20.x
```

运行一个测试容器确认一切正常：

```bash
docker run hello-world
```

如果看到 `Hello from Docker!` 就说明安装成功。

#### 第三步：配置 Docker 国内镜像加速（重要！）

在国内使用 Docker 拉取镜像可能很慢，需要配置镜像加速器。

**Docker Desktop（Windows/macOS）：**
1. 打开 Docker Desktop → 设置（齿轮图标）→ Docker Engine
2. 在 JSON 配置中添加 `registry-mirrors`：

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://docker.xuanyuan.me"
  ]
}
```

3. 点击 "Apply & Restart" 重启 Docker

> Docker 详细教程请参阅：[DOCKER.md](./DOCKER.md) 和 [deployment/DEPLOYMENT.md](./deployment/DEPLOYMENT.md)

---

### 1.6 Flutter SDK 安装与配置

#### 什么是 Flutter？

Flutter 是 Google 推出的跨平台应用开发框架。用一套代码，就能同时打包出 Android 和 iOS 两个平台的 App。本项目用它来开发无人机路径规划的移动客户端。

#### 第一步：下载 Flutter SDK

1. 访问：https://docs.flutter.dev/get-started/install
2. 选择你的操作系统，下载最新稳定版 SDK
3. 解压到你想放的位置：
   - Windows 推荐：`C:\tools\flutter`
   - macOS/Linux 推荐：`~/development/flutter`

> **重要**：路径不要有空格、不要有中文！例如不要放在 `C:\Program Files\` 下。

#### 第二步：配置环境变量

**Windows：**
1. 在 Path 环境变量中添加：`C:\tools\flutter\bin`

**macOS / Linux：**

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中
export PATH="$PATH:$HOME/development/flutter/bin"
```

#### 第三步：验证安装

重新打开终端，运行：

```bash
flutter doctor
```

这个命令会检查你的 Flutter 环境是否完整。输出会像一次体检报告，告诉你哪些 OK，哪些还需要修复。

**关键检查项及处理方式：**

| 检查项 | 状态要求 | 不满足时的处理 |
|--------|:-------:|---------------|
| Flutter SDK | ✅ | 检查环境变量是否正确 |
| Android toolchain | ✅ | 需要安装 Android Studio |
| Android Studio | ✅ | 安装 Android Studio 并安装 Android SDK |
| Visual Studio | ⚠️（仅 Windows 需要，用于 Windows 桌面开发，本项目不需要可忽略） | 不装也不影响 |
| Chrome | ✅ | 安装 Chrome 浏览器即可 |
| Connected device | ✅ | 连接 Android 手机或启动模拟器 |

> Flutter 环境详细配置请参阅：[uav-mobile-app 文档](../uav-mobile-app/README.md)

#### 第四步：安装 Android Studio（Flutter 开发必需）

1. 下载 Android Studio：https://developer.android.com/studio
2. 安装时选择 **Standard** 安装模式（会自动安装 Android SDK、模拟器等）
3. 启动 Android Studio → More Actions → SDK Manager
4. 在 SDK Platforms 中勾选 **Android 13.0 (API 33)** 或更高 → Apply
5. 在 SDK Tools 中勾选 **Android SDK Command-line Tools** → Apply

安装完成后，再次运行 `flutter doctor` 验证：

```bash
flutter doctor -v
```

期望看到大部分项目都是绿色对勾。如果有 Android 许可问题，运行：

```bash
flutter doctor --android-licenses
# 一路输入 y 同意许可
```

---

### 1.7 Python 环境配置

#### 第一步：安装 Python 3.8+

本项目中的 WRF 气象数据处理、贝叶斯数据同化等算法模块是用 Python 编写的。

1. 访问 Python 官网：https://www.python.org/downloads/
2. 下载 **Python 3.10** 或 **Python 3.11**（推荐，因为 3.12 尚有一些库未完全兼容）
3. **安装时务必勾选 "Add Python to PATH"**（将 Python 加入系统路径）

#### 第二步：验证安装

```bash
python --version
# Python 3.11.x

pip --version
# pip 23.x.x
```

#### 第三步：配置 pip 国内镜像源

```bash
# 永久设置清华源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 验证
pip config list
```

#### 第四步：了解 Python 虚拟环境（推荐）

虚拟环境可以隔离不同项目的 Python 依赖，避免版本冲突：

```bash
# 创建虚拟环境（在项目目录下）
cd d:\Developer\workplace\py\iteam\trae
python -m venv venv

# 激活虚拟环境
# Windows：
venv\Scripts\activate

# macOS/Linux：
source venv/bin/activate

# 激活后，命令行前会出现 (venv) 标识
# 退出虚拟环境：
deactivate
```

---

### 1.8 IDE 开发工具安装与配置

IDE（Integrated Development Environment，集成开发环境）就是写代码的"高级记事本"，有代码提示、调试、格式化等强大功能。

本项目推荐使用两个 IDE：

| IDE | 用途 | 免费？ |
|-----|------|:-----:|
| **IntelliJ IDEA Community** | Java 后端开发 | ✅ 免费 |
| **Visual Studio Code** | Vue 前端 + Flutter + Python | ✅ 免费 |

#### IntelliJ IDEA 安装

1. 下载 Community 版：https://www.jetbrains.com/idea/download/
2. 安装时勾选：
   - "Add 'Open Folder as Project'"（右键菜单打开项目）
   - "Add bin folder to PATH"
3. 完成安装后启动，跳过初始配置，选择 "Don't send"

**推荐安装的插件（打开 IDEA → File → Settings → Plugins）：**

| 插件名 | 作用 |
|--------|------|
| **Spring Boot Helper** | SpringBoot 开发辅助 |
| **Maven Helper** | Maven 依赖管理可视化 |
| **Lombok** | 简化 Java 代码（本项目大量使用） |
| **Chinese (Simplified) Language Pack** | IDEA 中文语言包（可选，方便英语不好的同学） |

#### Visual Studio Code 安装

1. 下载：https://code.visualstudio.com/
2. 安装后打开，推荐安装的插件（点击左侧方块图标）：

| 插件名 | 用途 |
|--------|------|
| **Vue - Official（Volar）** | Vue 3 开发支持 |
| **ESLint** | 代码规范检查 |
| **Prettier** | 代码自动格式化 |
| **Flutter** | Flutter 开发支持 |
| **Dart** | Dart 语言支持 |
| **Python** | Python 开发支持 |

---

### 1.9 Git 安装与配置

Git 是代码版本管理工具，用来从 GitHub 拉取（下载）项目源码。

#### 安装步骤

1. 下载：https://git-scm.com/downloads
2. 安装过程中保持默认选项即可，一直 "Next" 到底
3. 验证安装：

```bash
git --version
# git version 2.40.x
```

#### 配置用户名和邮箱（首次使用 Git 必须配置）

```bash
git config --global user.name "你的名字（拼音或英文）"
git config --global user.email "你的邮箱@example.com"
```

---

### 1.10 中间件安装（MySQL / Redis / Nacos / Kafka）

> **重要提示**：如果你已安装 Docker（本章 1.5 节），以下中间件都可以通过 Docker 一行命令启动，**强烈推荐用 Docker 方式**，省去复杂的手动安装过程。

#### 方式一：Docker 一键启动（推荐，仅需 2 分钟）

```bash
# 在项目根目录执行
cd d:\Developer\workplace\py\iteam\trae

# 仅启动基础设施（不启动微服务）
docker-compose up -d mysql redis nacos kafka

# 查看运行状态
docker-compose ps
```

一切搞定！四个中间件都会在后台运行。

#### 方式二：逐个手动安装（按需选择）

如果你不使用 Docker，以下是各中间件的手动安装指南。

##### MySQL 8.0 手动安装

**Windows：**
1. 下载 MySQL Installer：https://dev.mysql.com/downloads/installer/
2. 选择 "Developer Default" 安装模式
3. 设置 root 密码时，**记住你设的密码**（本项目配置文件中需要用到）
4. 安装完成后，MySQL 会作为 Windows 服务自动启动

**macOS：**

```bash
brew install mysql@8.0
brew services start mysql@8.0
```

**验证安装：**

```bash
mysql -u root -p
# 输入你设置的密码，看到 mysql> 提示符说明成功
```

**初始化本项目数据库：**

```sql
-- 创建本项目需要的 6 个数据库
CREATE DATABASE IF NOT EXISTS uav_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS wrf_processor DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS data_assimilation DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS meteor_forecast DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS path_planning DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS uav_weather DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建数据库用户并授权
CREATE USER IF NOT EXISTS 'uav'@'%' IDENTIFIED BY 'uav_password_2024';
GRANT ALL PRIVILEGES ON uav_platform.* TO 'uav'@'%';
GRANT ALL PRIVILEGES ON wrf_processor.* TO 'uav'@'%';
GRANT ALL PRIVILEGES ON data_assimilation.* TO 'uav'@'%';
GRANT ALL PRIVILEGES ON meteor_forecast.* TO 'uav'@'%';
GRANT ALL PRIVILEGES ON path_planning.* TO 'uav'@'%';
GRANT ALL PRIVILEGES ON uav_weather.* TO 'uav'@'%';
FLUSH PRIVILEGES;

-- 导入初始表结构
USE uav_platform;
SOURCE d:/Developer/workplace/py/iteam/trae/uav-path-planning-system/database/create_tables.sql;
```

> **注意**：将 `SOURCE` 命令中的路径改成你电脑上的实际路径。Windows 路径用正斜杠 `/`。

##### Redis 手动安装

**Windows（使用 Memurai，Redis 官方不直接支持 Windows）：**
- 下载 Memurai：https://www.memurai.com/get-memurai
- 安装后自动作为 Windows 服务运行

**macOS：**

```bash
brew install redis
brew services start redis
```

**验证 Redis 是否运行：**

```bash
redis-cli ping
# 应返回：PONG
```

##### Nacos 手动安装

1. 下载 Nacos 2.3.0：https://github.com/alibaba/nacos/releases/tag/2.3.0
2. 解压后进入目录，运行：

**Windows：**

```cmd
cd nacos\bin
startup.cmd -m standalone
```

**macOS/Linux：**

```bash
cd nacos/bin
sh startup.sh -m standalone
```

3. 启动后访问 Nacos 控制台：http://localhost:8848/nacos
   - 默认用户名：`nacos`
   - 默认密码：`nacos`

##### Kafka 手动安装

1. 下载 Kafka：https://kafka.apache.org/downloads（选择 Binary 版本）
2. 解压后，按以下顺序启动：

```bash
# 第一步：启动 Zookeeper（Kafka 依赖它管理集群状态）
# Windows：
bin\windows\zookeeper-server-start.bat config\zookeeper.properties

# macOS/Linux：
bin/zookeeper-server-start.sh config/zookeeper.properties

# 第二步：新开一个终端，启动 Kafka
# Windows：
bin\windows\kafka-server-start.bat config\server.properties

# macOS/Linux：
bin/kafka-server-start.sh config/server.properties
```

> **Kafka 默认端口**：9092

---

### 1.11 环境搭建完成检查清单

安装完成后，请逐项确认以下所有工具都能正常运行：

```
  JDK 17   →  java -version 显示 17.x
  Maven    →  mvn -version 显示 3.9.x，Java version: 17
  Node.js  →  node -v 显示 v18.x，npm -v 显示 9.x
  Docker   →  docker --version && docker run hello-world
  Flutter  →  flutter doctor 大部分项为绿色对勾
  Python   →  python --version 显示 3.10+，pip --version 正常
  Git      →  git --version 显示 2.40+
  MySQL    →  mysql -u root -p 能登录（或 Docker 在运行）
  Redis    →  redis-cli ping 返回 PONG（或 Docker 在运行）
  Nacos    →  http://localhost:8848/nacos 能打开
  Kafka    →  netstat -an | findstr 9092 能看到端口监听
  IDEA     → 能启动，能创建 Java 项目
  VS Code  → 能启动，能打开文件夹
```

**如果全部通过**，恭喜你！环境搭建完毕，可以进入第二章了。

---

## 第二章：源码获取 —— 把代码拿下来

### 2.1 项目拉取

#### 第一步：克隆项目到本地

打开终端，进入你想要存放项目的目录，执行：

```bash
# 假设你想把项目放在 d:\Developer\workplace\py\
cd d:\Developer\workplace\py

# 克隆项目（下载代码）
git clone https://github.com/602420232-dotcom/weather.git

# 克隆完成后，进入项目目录
cd trae
```

> **如果 `git clone` 速度很慢**，可以尝试使用国内镜像加速：
> ```bash
> git clone https://gitclone.com/github.com/602420232-dotcom/weather.git
> ```

#### 第二步：切换到开发分支

```bash
# 查看所有分支
git branch -a

# 切换到主开发分支
git checkout main
```

#### 第三步：确认项目完整性

```bash
# 列出根目录下的文件和文件夹
dir   # Windows
ls -la  # macOS/Linux
```

你应该能看到类似这样的结构：

```
trae/
├── api-gateway/                    # API 网关
├── common-dependencies/            # 公共依赖管理
├── common-utils/                   # 公共工具库
├── data-assimilation-platform/     # 数据同化平台（Python + Spring）
├── data-assimilation-service/      # 数据同化微服务
├── deployments/                    # 部署配置
├── docs/                           # 项目文档
├── edge-cloud-coordinator/         # 边云协同框架
├── meteor-forecast-service/        # 气象预测微服务
├── path-planning-service/          # 路径规划微服务
├── scripts/                        # 运维脚本
├── tests/                          # 测试
├── uav-edge-sdk/                   # 边缘端 SDK (C++)
├── uav-mobile-app/                 # Flutter 移动端
├── uav-path-planning-system/       # 路径规划全栈系统 (Spring + Vue)
├── uav-platform-service/           # 主平台微服务
├── uav-weather-collector/          # 气象收集微服务
├── wrf-processor-service/          # WRF 处理微服务
├── docker-compose.yml              # Docker 编排主文件
├── docker-compose.dev.yml          # 开发环境编排
├── pom.xml                         # Maven 聚合 POM
└── README.md                       # 项目总说明
```

---

### 2.2 项目目录结构详解

#### 顶层目录速查表

| 目录/文件 | 类型 | 一句话说明 |
|-----------|:----:|-----------|
| `api-gateway/` | 微服务 | 所有请求的统一入口，负责路由转发、限流、熔断 |
| `common-dependencies/` | POM 工程 | 统一管理所有微服务的依赖版本号 |
| `common-utils/` | 工具库 | 被所有微服务共享的安全、审计、JWT 等工具 |
| `data-assimilation-platform/` | 平台 | 贝叶斯数据同化算法平台（含 Python 算法核心 + Spring 服务） |
| `data-assimilation-service/` | 微服务 | 数据同化 REST API 服务 |
| `deployments/` | 配置 | Docker、K8s、监控、边端、流处理等部署编排文件 |
| `docs/` | 文档 | 项目完整文档中心 |
| `edge-cloud-coordinator/` | 微服务 | 边云协同，负责边缘设备与云端通信 |
| `meteor-forecast-service/` | 微服务 | 气象预测与订正（LSTM + XGBoost） |
| `path-planning-service/` | 微服务 | 路径规划算法服务（VRPTW + DE-RRT* + DWA + A*） |
| `scripts/` | 脚本 | 构建、部署、集群管理等运维脚本 |
| `tests/` | 测试 | 集成测试、负载测试、性能测试 |
| `uav-edge-sdk/` | SDK | 边缘端设备 SDK（C++14 + pybind11） |
| `uav-mobile-app/` | Flutter App | 移动端跨平台客户端 |
| `uav-path-planning-system/` | 全栈系统 | 路径规划完整系统（含 Spring 后端 + Vue 前端） |
| `uav-platform-service/` | 微服务 | 主平台服务，负责服务编排、数据源管理等 |
| `uav-weather-collector/` | 微服务 | 多源气象数据采集与融合 |
| `wrf-processor-service/` | 微服务 | WRF 气象数据处理（预处理、后处理、可视化） |
| `docker-compose.yml` | 配置 | Docker 服务编排主文件 |
| `pom.xml` | Maven | 根聚合 POM，统一构建所有 Java 模块 |

> 详细的项目结构说明请参阅：[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

---

### 2.3 各模块职责说明

#### 微服务完整清单

本项目采用 **微服务架构**（把大系统拆成 10 个独立小服务），各服务之间通过 HTTP 接口互相调用：

| 序号 | 服务名称 | 端口 | 数据库 | 核心职责 |
|:----:|---------|:----:|--------|---------|
| 1 | **api-gateway** | **8088** | 无 | 统一入口、路由转发、限流熔断、请求鉴权 |
| 2 | **uav-platform-service** | **8080** | uav_platform | 主平台编排，无人机管理、任务调度、数据源管理 |
| 3 | **wrf-processor-service** | **8081** | wrf_processor | WRF 数值天气预报数据的预处理、后处理、可视化 |
| 4 | **meteor-forecast-service** | **8082** | meteor_forecast | LSTM + XGBoost 气象预测与深度学习订正 |
| 5 | **path-planning-service** | **8083** | path_planning | VRPTW + DE-RRT* + DWA + A* 路径规划算法 |
| 6 | **data-assimilation-service** | **8084** | data_assimilation | 3D-VAR / 4D-VAR / EnKF / Hybrid 数据同化 |
| 7 | **uav-weather-collector** | **8086** | uav_weather | 多源气象数据采集、清洗、融合 |
| 8 | **edge-cloud-coordinator** | **8000** | 无 | 边云协同，REST(8000) + WebSocket(8765) 双通道 |
| 9 | **backend-spring** | **8089** | uav_path_planning | 独立路径规划后端，含用户认证授权 RBAC |
| 10 | **service_spring** | **8094** | — | 贝叶斯同化服务（data-assimilation-platform 子模块） |

#### 基础设施中间件

| 中间件 | 端口 | 用途 |
|--------|:----:|------|
| **MySQL 8.0** | 3306 | 关系型数据库，存储所有业务数据 |
| **Redis 6.2** | 6379 | 高性能缓存，加速数据读取、存储会话 |
| **Nacos 2.3.0** | 8848 | 服务注册发现（让服务互相找到）+ 配置中心（统一管理配置） |
| **Kafka 3.6** | 9092 | 消息队列，实现服务间异步通信和解耦 |

#### 前端 & 移动端

| 应用 | 技术栈 | 开发端口 | 说明 |
|------|--------|:------:|------|
| **Vue 3 前端** | Vue 3.4 + Vite 5 + Ant Design Vue 4 | **3000** | Web 管理界面，含地图、仪表盘、飞行监控 |
| **Flutter 移动端** | Flutter 3.2+ + Riverpod + Dio | 由 Flutter 自动分配 | 跨平台 APP，同时支持 Android 和 iOS |

> 更多架构细节请参阅：[architecture.md](./architecture.md)

---

## 第二章快速自检

在进入第三章之前，请确认你已完成以下操作：

```bash
# 1. 确认 JDK 17
java -version   # 应输出 17.x.x

# 2. 确认 Maven
mvn -version    # 应包含 Java version: 17

# 3. 确认 Node.js
node -v         # 应输出 v18.x.x
npm -v          # 应输出 9.x.x

# 4. 确认 Docker
docker --version

# 5. 确认项目目录结构
cd d:\Developer\workplace\py\iteam\trae
dir             # 应看到 api-gateway/、uav-platform-service/ 等目录
```

---

## 第三章：模块开发 —— 开始写代码

> **导读**：这一章是本指南最核心的部分。我们将依次学习 Java 基础、SpringBoot 微服务开发、Maven 多模块管理、Vue 前端开发、Flutter 移动端开发。每个小节都有可运行的代码示例。

### 3.1 Java 17 必备基础知识点

#### 3.1.1 零基础 Java 速成（15 分钟）

如果你完全没接触过 Java，这里用最短的时间让你能看懂项目代码。

**① 什么是类（Class）和对象（Object）？**

用一个比喻：类是"汽车设计图纸"，对象是"根据图纸造出来的真车"。

```java
// 这是一个"类"（设计图纸）
public class Drone {
    String name;      // 属性：无人机名字
    double battery;   // 属性：电池电量

    // 构造函数：制造无人机的"工厂"
    public Drone(String name, double battery) {
        this.name = name;
        this.battery = battery;
    }

    // 方法：无人机能做的"动作"
    public void fly() {
        System.out.println(name + " 正在飞行，电量：" + battery + "%");
    }
}

// 使用类
Drone myDrone = new Drone("侦察一号", 95.0);  // 造一架"对象"
myDrone.fly();  // 输出：侦察一号 正在飞行，电量：95.0%
```

**② 项目中最常见的注解（Annotation，标记）**

注解就是给代码贴标签，SpringBoot 根据标签自动做事情。就像快递包裹上的"易碎品"标签，快递员看到就会轻拿轻放。

| 注解 | 通俗含义 | 用在哪里 |
|------|---------|---------|
| `@RestController` | "这是一个接口类，负责接收和返回数据" | Controller 类 |
| `@Service` | "这是一个业务逻辑类" | Service 类 |
| `@Autowired` | "帮我把这个依赖自动注入进来" | 字段/构造函数 |
| `@RequestMapping` | "这个接口的网址是 xxx" | 方法 |
| `@Data` | "自动生成 getter、setter、toString 方法"（Lombok） | 实体类 |
| `@Component` | "这个类交给 Spring 管理" | 工具类 |

**③ 项目中用到的数据结构**

```java
// List —— 有序列表，像购物清单
List<String> droneNames = Arrays.asList("侦察一号", "侦察二号", "运输一号");

// Map —— 键值对，像字典
Map<String, Object> params = new HashMap<>();
params.put("lat", 31.2304);  // 纬度
params.put("lon", 121.4737); // 经度

// DTO（Data Transfer Object）—— 数据传输对象，前端传过来的数据
// 项目中到处可见，例：
public class PathPlanningRequest {
    private Double startLat;
    private Double startLon;
    private Double endLat;
    private Double endLon;
}
```

> **推荐学习资源**：如果你觉得 Java 基础还不够，建议配合阅读 [Java 17 官方文档](https://docs.oracle.com/en/java/javase/17/)。本项目的 Java 代码规范遵循 [architecture.md](./architecture.md) 中的约定。

---

### 3.2 SpringBoot 微服务核心架构原理

#### 3.2.1 什么是 SpringBoot？（用一个比喻理解）

如果你要开一家餐厅，需要自己建厨房、找厨师、设计菜单、管理食材……现在 SpringBoot 给你一个"集成式厨房"：灶台、冰箱、油烟机全部装好，你只需要炒菜就行了。

- **传统开发**：自己配置 Tomcat（Web 服务器）、自己写 XML 配置、自己管理依赖
- **用 SpringBoot**：一切开箱即用，写 5 行代码就能跑一个 Web 接口

#### 3.2.2 项目微服务架构全景图

```
用户（浏览器 / APP）
    │
    ▼
┌─────────────────────────────────────┐
│         API Gateway (8088)          │  ← 统一入口，负责路由转发、限流、鉴权
│     Spring Cloud Gateway            │
└──────┬──────┬──────┬──────┬─────────┘
       │      │      │      │
       ▼      ▼      ▼      ▼
   ┌──────┐┌──────┐┌──────┐┌──────┐
   │平台服务││WRF处理││路径规划││气象预测│  ...共 10 个微服务
   │8080  ││8081  ││8083  ││8082  │
   └──┬───┘└──┬───┘└──┬───┘└──┬───┘
      │       │       │       │
      ▼       ▼       ▼       ▼
   ┌──────────────────────────────────┐
   │  Nacos (8848)  ← 服务注册发现    │
   │  MySQL (3306)  ← 数据库         │
   │  Redis (6379)  ← 缓存           │
   │  Kafka (9092)  ← 消息队列       │
   └──────────────────────────────────┘
```

#### 3.2.3 一个微服务的最小可运行结构（以 uav-platform-service 为例）

```
uav-platform-service/
├── pom.xml                           # Maven 配置，声明依赖和父工程
├── src/main/java/com/uav/platform/
│   ├── PlatformApplication.java      # 启动类（SpringBoot 入口）
│   ├── controller/                   # 控制器层 —— 接收请求，返回结果
│   │   ├── PlatformController.java
│   │   └── DataSourceController.java
│   ├── service/                      # 服务层 —— 核心业务逻辑
│   │   ├── PlatformService.java
│   │   └── impl/
│   │       └── PlatformServiceImpl.java
│   ├── repository/                   # 数据访问层 —— 操作数据库
│   │   └── DataSourceRepository.java
│   ├── entity/                       # 实体类 —— 对应数据库表
│   │   └── DataSource.java
│   └── config/                       # 配置类
│       └── ResilienceConfig.java
└── src/main/resources/
    ├── application.yml               # 应用配置文件
    └── bootstrap.yml                 # 启动配置（连接 Nacos）
```

**启动类示例** —— 这就是整个服务的"开关"：

```java
package com.uav.platform;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication          // 标记：这是 SpringBoot 应用
@EnableDiscoveryClient          // 标记：注册到 Nacos
public class PlatformApplication {
    public static void main(String[] args) {
        SpringApplication.run(PlatformApplication.class, args);
    }
}
```

**Controller 示例** —— 这就是"接口地址"：

```java
@RestController
@RequestMapping("/api/v1/platform")
public class PlatformController {

    @Autowired
    private PlatformService platformService;

    // GET 请求：查询无人机状态
    // 访问地址：http://localhost:8080/api/v1/platform/drones
    @GetMapping("/drones")
    public List<Drone> getAllDrones() {
        return platformService.getAllDrones();
    }

    // POST 请求：创建任务
    // 访问地址：http://localhost:8080/api/v1/platform/tasks
    @PostMapping("/tasks")
    public Task createTask(@RequestBody TaskRequest request) {
        return platformService.createTask(request);
    }
}
```

> **分层职责口诀**：Controller 管"接客送客"（接收请求、返回响应），Service 管"做事"（业务逻辑），Repository 管"存数据"（操作数据库）。每层只做自己的事，不越界。

#### 3.2.4 配置文件核心参数说明

每个微服务都有一个 `application.yml`，这是该服务的"身份证"和"通讯录"：

```yaml
# application.yml —— 以 uav-platform-service 为例
server:
  port: 8080                          # 【自定义】本服务的端口号

spring:
  application:
    name: uav-platform-service        # 【自定义】服务名称（Nacos 中显示的）
  datasource:
    url: jdbc:mysql://localhost:3306/uav_platform?useUnicode=true&characterEncoding=utf8mb4
    username: uav                     # 【自定义】数据库用户名
    password: uav_password_2024       # 【自定义】数据库密码
  redis:
    host: localhost                   # Redis 地址，Docker 部署时改为容器名
    port: 6379
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848   # Nacos 注册中心地址
      config:
        server-addr: localhost:8848   # Nacos 配置中心地址

# 启用熔断器（服务保护机制，防止故障扩散）
resilience4j:
  circuitbreaker:
    configs:
      default:
        sliding-window-size: 10      # 统计窗口大小
        failure-rate-threshold: 50   # 熔断阈值：50% 失败就熔断
```

> **配置修改说明**：将所有 `localhost` 改成你的实际地址。用 Docker 部署时，`localhost` 要改成 Docker 容器名（如 `mysql`、`redis`、`nacos`）。

---

### 3.3 Maven 依赖管理与多模块配置详解

#### 3.3.1 Maven 多模块项目是怎么组织起来的？

本项目用 Maven 管理 10+ 个 Java 模块。如果每个模块各自管理依赖，就会出现"A 模块用 SpringBoot 3.3，B 模块用 3.4"的混乱局面。

解决方案：**父 POM 统一管理**。

```
trae/pom.xml                     ← 根聚合 POM（父工程），定义所有公共版本号
├── common-dependencies/pom.xml  ← BOM 工程，集中管理所有依赖版本
├── common-utils/pom.xml         ← 子模块，继承父 POM
├── api-gateway/pom.xml
├── uav-platform-service/pom.xml
├── wrf-processor-service/pom.xml
├── ...
└── uav-path-planning-system/
    └── backend-spring/pom.xml
```

#### 3.3.2 根聚合 POM 的核心结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <!-- 父工程坐标 -->
    <groupId>com.uav</groupId>
    <artifactId>uav-parent</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>       <!-- 注意：父工程必须是 pom 类型 -->

    <!-- 定义所有子模块 -->
    <modules>
        <module>common-dependencies</module>
        <module>common-utils</module>
        <module>api-gateway</module>
        <module>uav-platform-service</module>
        <module>wrf-processor-service</module>
        <module>meteor-forecast-service</module>
        <module>path-planning-service</module>
        <module>data-assimilation-service</module>
        <module>uav-weather-collector</module>
    </modules>

    <!-- 统一 Spring 生态版本 -->
    <properties>
        <java.version>17</java.version>
        <spring-boot.version>3.5.14</spring-boot.version>
        <spring-cloud.version>2025.0.2</spring-cloud.version>
        <spring-cloud-alibaba.version>2025.0.0.0</spring-cloud-alibaba.version>
    </properties>
</project>
```

#### 3.3.3 Maven 常用命令大全

| 命令 | 作用 | 实际使用场景 |
|------|------|-------------|
| `mvn clean` | 清空上次编译的文件 | 遇到奇怪报错时先 clean 再编译 |
| `mvn compile` | 编译源代码 | 检查代码是否有语法错误 |
| `mvn package -DskipTests` | 打包成 jar（跳过测试） | 要部署时使用 |
| `mvn install -U` | 将模块安装到本地仓库并强制更新依赖 | 依赖下载不完整时 |
| `mvn spring-boot:run` | 直接运行 SpringBoot 应用 | 本地开发启动单个服务 |
| `mvn clean package -pl api-gateway -am` | 只打包指定模块（含其依赖） | 只改了一个服务时不用全量构建 |
| `mvn dependency:tree` | 查看依赖树 | 排查依赖冲突 |
| `mvn clean install -U -DskipTests` | 终极刷新命令 | 依赖下载出错时的"万能药" |

> 更多 Maven 问题请参阅：[MAVEN_FIX.md](./MAVEN_FIX.md)

---

### 3.4 后端微服务模块开发实战

#### 3.4.1 启动第一个微服务（uav-platform-service）

**第 1 步：确保基础设施已就绪**

```bash
# 用 Docker 启动 MySQL、Redis、Nacos
cd d:\Developer\workplace\py\iteam\trae
docker-compose up -d mysql redis nacos
```

**第 2 步：初始化数据库**

```bash
# 连接 MySQL（密码在 .env 文件或 .env.example 中查看）
mysql -h localhost -P 3306 -u root -p

# 导入表结构
SOURCE d:/Developer/workplace/py/iteam/trae/uav-path-planning-system/database/create_tables.sql;
```

**第 3 步：编译并启动服务**

```bash
cd d:\Developer\workplace\py\iteam\trae

# 方法一：Maven 命令启动（推荐）
mvn spring-boot:run -pl uav-platform-service

# 方法二：在 IDEA 中启动
# 打开 IDEA → File → Open → 选择 trae 目录
# 在右侧 Maven 面板中找到 uav-platform-service → Plugins → spring-boot → spring-boot:run
```

**第 4 步：验证服务是否启动成功**

```bash
# 新开一个终端
curl http://localhost:8080/actuator/health

# 预期返回：{"status":"UP"}
```

如果看到 `{"status":"UP"}`，恭喜！你的第一个微服务启动成功了。

#### 3.4.2 按顺序启动所有微服务

**推荐的启动顺序**（先基础设施，再微服务，最后网关）：

```
1. MySQL、Redis、Nacos、Kafka  ← 基础设施
2. backend-spring (8089)        ← 独立服务，不依赖其他微服务
3. uav-platform-service (8080)  ← 主平台
4. wrf-processor-service (8081)
5. meteor-forecast-service (8082)
6. path-planning-service (8083)
7. data-assimilation-service (8084)
8. uav-weather-collector (8086)
9. api-gateway (8088)           ← 网关最后启动
```

**一键启动所有服务脚本（Windows PowerShell）：**

```powershell
# 保存为 start-all-services.ps1
$services = @(
    @{Name="backend-spring"; Port=8089},
    @{Name="uav-platform-service"; Port=8080},
    @{Name="wrf-processor-service"; Port=8081},
    @{Name="meteor-forecast-service"; Port=8082},
    @{Name="path-planning-service"; Port=8083},
    @{Name="data-assimilation-service"; Port=8084},
    @{Name="uav-weather-collector"; Port=8086},
    @{Name="api-gateway"; Port=8088}
)

foreach ($svc in $services) {
    Write-Host "启动 $($svc.Name) ..."
    Start-Process -NoNewWindow mvn -ArgumentList "spring-boot:run -pl $($svc.Name)" -WorkingDirectory "d:\Developer\workplace\py\iteam\trae"
    Start-Sleep -Seconds 15  # 等待服务启动
}

Write-Host "所有服务启动完成！"
Write-Host "API Gateway: http://localhost:8088"
Write-Host "Platform Service: http://localhost:8080"
```

> **注意**：在本地开发时，不需要启动所有 10 个服务。根据你要调试的功能只启动对应的 2~3 个服务即可，可以大大节省电脑资源。

---

### 3.5 数据库设计与连接配置

#### 3.5.1 本项目 6 个数据库的分工

每个微服务有自己专属的数据库，互不干扰：

| 数据库名 | 所属微服务 | 核心表 | 说明 |
|----------|-----------|--------|------|
| `uav_platform` | uav-platform-service (8080) | users, drones, tasks, data_sources | 用户、无人机、任务管理 |
| `wrf_processor` | wrf-processor-service (8081) | wrf_data, wrf_jobs | WRF 气象数据存储 |
| `meteor_forecast` | meteor-forecast-service (8082) | forecasts, models | 预测结果与模型信息 |
| `path_planning` | path-planning-service (8083) | paths, waypoints, obstacles | 路径规划结果 |
| `data_assimilation` | data-assimilation-service (8084) | assimilation_results | 数据同化结果 |
| `uav_weather` | uav-weather-collector (8086) | weather_records, stations | 气象采集数据 |

#### 3.5.2 各服务的 JDBC 连接配置

```yaml
# uav-platform-service 的 application.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/uav_platform?useUnicode=true&characterEncoding=utf8mb4&serverTimezone=Asia/Shanghai
    username: uav                  # 【自定义】改成你的数据库用户名
    password: uav_password_2024    # 【自定义】改成你的数据库密码
    driver-class-name: com.mysql.cj.jdbc.Driver

# wrf-processor-service 的 application.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/wrf_processor?useUnicode=true&characterEncoding=utf8mb4&serverTimezone=Asia/Shanghai
    username: uav
    password: uav_password_2024
```

> **Docker 部署时的地址变化**：容器之间通信不能用 `localhost`，要用容器名。例如 `jdbc:mysql://mysql:3306/uav_platform`

---

### 3.6 Nacos 服务注册与配置中心接入

#### 3.6.1 Nacos 是什么？（一句话解释）

Nacos = 微服务的"电话本" + "云记事本"。

- **服务注册/发现**（电话本）：微服务 A 启动后会说"我叫 uav-platform-service，我的地址是 xxx:8080"。微服务 B 需要调用 A 时，去 Nacos 查"电话本"找到 A 的地址。
- **配置中心**（云记事本）：把所有微服务的配置统一存放在 Nacos，修改一处全部生效，不需要逐个改配置文件。

#### 3.6.2 访问 Nacos 控制台

1. 确保 Nacos 已启动（Docker 或手动）
2. 浏览器打开：http://localhost:8848/nacos
3. 默认用户名/密码：`nacos` / `nacos`
4. 在"服务管理"→"服务列表"中可以看到所有已注册的微服务

#### 3.6.3 微服务接入 Nacos 的配置

每个微服务需要添加以下配置和依赖：

**① 添加 Maven 依赖（在对应模块的 pom.xml 中）：**

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
</dependency>
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
</dependency>
```

**② 配置 bootstrap.yml：**

```yaml
# bootstrap.yml —— 注意是 bootstrap.yml 不是 application.yml！
# 原因：bootstrap.yml 优先级更高，先于 application.yml 加载，
# 这样 Nacos 配置可以在应用启动的最早阶段就生效

spring:
  application:
    name: uav-platform-service    # 【自定义】改成你的服务名
  cloud:
    nacos:
      discovery:
        server-addr: localhost:8848    # Nacos 地址
        namespace:                     # 【自定义】命名空间 ID（多环境隔离时用）
      config:
        server-addr: localhost:8848
        file-extension: yaml          # 配置文件格式
```

**③ 在启动类上加注解：**

```java
@SpringBootApplication
@EnableDiscoveryClient   // ← 加这一行，告诉 Spring：我去 Nacos 注册
public class PlatformApplication { ... }
```

#### 3.6.4 验证服务注册成功

启动微服务后，打开 Nacos 控制台 http://localhost:8848/nacos ，在"服务管理→服务列表"中应该能看到你的服务名，状态为"健康"。

```bash
# 也可以用命令行验证
curl -X GET "http://localhost:8848/nacos/v1/ns/instance/list?serviceName=uav-platform-service"

# 返回 JSON 中包含服务实例信息，说明注册成功
```

---

### 3.7 Redis 缓存与 Kafka 消息队列使用

#### 3.7.1 Redis 缓存实战

**Redis 是什么？** Redis 是一个"超快内存数据库"。MySQL 数据存在硬盘，读取需要几十毫秒；Redis 数据存在内存，读取仅需不到 1 毫秒。

**在本项目中的应用场景：**
- 缓存频繁查询的无人机状态（减少数据库压力）
- 存储用户登录 Token（JWT）
- API 网关的限流计数器
- 临时数据（如验证码）

**SpringBoot 中使用 Redis：**

```java
@Service
public class DroneCacheService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    // 缓存无人机状态，设置 5 分钟过期
    public void cacheDroneStatus(String droneId, String status) {
        String key = "drone:status:" + droneId;
        redisTemplate.opsForValue().set(key, status, 5, TimeUnit.MINUTES);
    }

    // 查询缓存的无人机状态
    public String getDroneStatus(String droneId) {
        String key = "drone:status:" + droneId;
        return (String) redisTemplate.opsForValue().get(key);
    }
}
```

**验证 Redis 连接：**

```bash
# 连接 Redis
redis-cli -h localhost -p 6379

# 查看所有 key
keys *

# 查看特定 key 的值
get drone:status:001
```

#### 3.7.2 Kafka 消息队列实战

**Kafka 是什么？** Kafka 是一个"消息中转站"。想象一下快递分拣中心：发件人（Producer）把包裹放到传送带（Topic），分拣系统把包裹分发给不同的收件人（Consumer）。

**在本项目中的应用场景：**
- 边云协同：边缘设备采集的气象数据通过 Kafka 发送给云端
- 异步任务：路径规划计算结果通过 Kafka 通知前端
- 日志收集：各服务的运行日志统一发送到 Kafka

**SpringBoot 中使用 Kafka：**

```java
// 生产者：发送消息
@Service
public class WeatherDataProducer {

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    public void sendWeatherData(String data) {
        // Topic 名称：weather-data（在 Kafka 中相当于"频道"）
        kafkaTemplate.send("weather-data", data);
    }
}

// 消费者：接收消息
@Component
public class WeatherDataConsumer {

    @KafkaListener(topics = "weather-data", groupId = "weather-group")
    public void receiveWeatherData(String message) {
        System.out.println("收到气象数据：" + message);
        // 在这里处理收到的数据
    }
}
```

**Kafka 常用命令：**

```bash
# 创建 Topic（消息主题）
kafka-topics.sh --create --topic weather-data --bootstrap-server localhost:9092

# 查看所有 Topic
kafka-topics.sh --list --bootstrap-server localhost:9092

# 发送测试消息
kafka-console-producer.sh --topic weather-data --bootstrap-server localhost:9092

# 接收消息
kafka-console-consumer.sh --topic weather-data --from-beginning --bootstrap-server localhost:9092
```

---

### 3.8 Vue 前端项目开发指南

#### 3.8.1 前端项目技术栈

| 技术 | 版本 | 作用 |
|------|:----:|------|
| **Vue 3** | 3.4.0 | 前端框架（组织页面结构） |
| **Vite** | 5.0.0 | 构建工具（"编译打包器"，比 Webpack 快很多） |
| **Ant Design Vue** | 4.0.0 | UI 组件库（按钮、表格、弹窗等现成组件） |
| **Axios** | 1.6.2 | HTTP 请求库（前端和后端"打电话"的工具） |
| **Leaflet** | 1.9.4 | 地图组件（展示无人机飞行轨迹） |
| **Cesium** | 1.119.0 | 3D 地球组件（三维可视化） |
| **ECharts** | 5.4.3 | 图表库（展示气象数据图表） |

#### 3.8.2 前端项目目录结构

```
uav-path-planning-system/frontend-vue/
├── index.html                       # 入口 HTML 文件
├── package.json                     # npm 依赖声明
├── vite.config.js                   # Vite 配置（端口、代理等）
├── src/
│   ├── main.js                      # Vue 应用入口
│   ├── App.vue                      # 根组件
│   ├── router/                      # 路由配置（定义页面地址）
│   │   └── index.js
│   ├── views/                       # 页面组件（一个路由对应一个页面）
│   │   ├── Dashboard.vue            # 仪表盘首页
│   │   ├── DroneMonitor.vue         # 无人机监控页
│   │   ├── PathPlanning.vue         # 路径规划页
│   │   ├── WeatherData.vue          # 气象数据页
│   │   └── Login.vue                # 登录页
│   ├── components/                  # 可复用组件（页面中的"零件"）
│   │   ├── MapViewer.vue            # 地图组件
│   │   └── StatusCard.vue           # 状态卡片
│   ├── api/                         # API 接口定义
│   │   └── index.js                 # Axios 封装和接口方法
│   └── assets/                      # 静态资源（图片、CSS）
└── public/                          # 公共静态文件
```

#### 3.8.3 启动前端开发服务器

```bash
# 1. 进入前端项目目录
cd d:\Developer\workplace\py\iteam\trae\uav-path-planning-system\frontend-vue

# 2. 安装依赖（首次运行必须执行）
npm install

# 3. 启动开发服务器
npm run dev

# 看到类似输出说明成功：
#   VITE v5.0.0  ready in 1234 ms
#   ➜  Local:   http://localhost:3000/
```

浏览器访问 http://localhost:3000 即可看到前端页面。

#### 3.8.4 前端如何调用后端接口（以登录为例）

```javascript
// src/api/index.js —— 接口封装文件

import axios from 'axios'

// 创建 Axios 实例（配置公共参数）
const request = axios.create({
  baseURL: '/api',         // 所有请求都以 /api 开头
  timeout: 10000           // 10 秒超时
})

// 【请求拦截器】每次发请求前自动加上 Token
request.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// 【响应拦截器】统一处理错误
request.interceptors.response.use(
  response => response.data,
  error => {
    console.error('请求失败:', error)
    return Promise.reject(error)
  }
)

// ===== 业务接口 =====

// 用户登录
export function login(username, password) {
  return request.post('/v1/auth/login', { username, password })
}

// 获取无人机列表
export function getDroneList() {
  return request.get('/v1/platform/drones')
}

// 提交路径规划请求
export function planPath(params) {
  return request.post('/v1/planning/path', params)
}
```

```javascript
// 在页面中使用
import { login, getDroneList } from '@/api/index'

// 登录
async function handleLogin() {
  const result = await login('admin', 'password')
  localStorage.setItem('token', result.token)
}

// 获取无人机列表
async function loadDrones() {
  const drones = await getDroneList()
  console.log('无人机列表:', drones)
}
```

#### 3.8.5 Vite 代理配置（解决跨域问题）

开发时前端（3000 端口）调用后端（8080 端口）会遇到跨域限制。Vite 代理帮我们绕过这个限制：

```javascript
// vite.config.js
export default defineConfig({
  server: {
    port: 3000,     // 前端开发端口
    proxy: {
      '/api': {     // 所有 /api 开头的请求都会被代理
        target: 'http://localhost:8088',  // 代理到 API Gateway
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')  // 去掉 /api 前缀
      }
    }
  }
})
```

> **原理**：浏览器请求 `http://localhost:3000/api/v1/drones` → Vite 服务器转发到 `http://localhost:8088/v1/drones` → API Gateway 路由到对应微服务

#### 3.8.6 Cesium 3D 地图配置（智能驾驶舱所需，可选）

> **注意**：Cesium 仅用于智能驾驶舱（`/smart-cockpit`）的 3D AR 数字地图功能。如果不需要 3D 地图，可跳过本节。

**第一步：获取 Cesium Ion Access Token**

Cesium 的全球影像底图和 3D Tiles 地形服务需要 Access Token（免费注册即可）：

1. 浏览器打开 https://ion.cesium.com/signin ，用 GitHub/Google 账号注册
2. 登录后进入 **Access Tokens** 页面，复制默认 Token
3. 打开项目中的 `.env` 文件，将 Token 粘贴进去：

```bash
# uav-path-planning-system/frontend-vue/.env
VITE_CESIUM_ION_TOKEN=eyJhbGciOiJIUzI1NiIs...你的真实Token
```

```bash
# uav-path-planning-system/frontend-vue/.env.production
VITE_CESIUM_ION_TOKEN=eyJhbGciOiJIUzI1NiIs...你的真实Token
```

**第二步：安装依赖**（若此前已执行则跳过）

```bash
cd uav-path-planning-system/frontend-vue
npm install
```

**第三步：启动开发服务器**

```bash
npm run dev
```

首次启动时会自动执行 `scripts/copy-cesium-assets.cjs` 脚本，将 Cesium 的 `Workers/`、`Assets/`、`Widgets/`、`ThirdParty/` 复制到 `public/cesium/` 目录。之后访问 `http://localhost:3000/smart-cockpit` 即可看到 3D 驾驶舱。

**若 Cesium 未正常加载：**

| 现象 | 原因 | 解决 |
|------|------|------|
| 3D 地球无法显示 | Token 未配置或无效 | 检查 `.env` 中的 `VITE_CESIUM_ION_TOKEN` |
| 页面报错 "Cesium is not defined" | 静态资源未复制 | 手动执行 `npm run copy-cesium` |
| 生产构建后 3D 空白 | Token 仅配了 `.env` 未配 `.env.production` | 将 Token 同步到 `.env.production` |

> **构建优化说明**：Cesium 库体积较大（~30MB），Vite 配置中已将 Cesium 单独分离为 `cesium` chunk、关闭 sourcemap、提高 chunk 体积警告阈值到 1500KB，确保生产构建高效稳定。详细配置见 `frontend-vue/README.md` 的"Cesium 3D 地图配置"章节。

---

### 3.9 Flutter 移动端开发指南

#### 3.9.1 Flutter 是什么？（通俗解释）

Flutter 是 Google 开发的跨平台框架。用一套代码同时生成 Android APP 和 iOS APP，不需要分别学 Android（Kotlin/Java）和 iOS（Swift）。

#### 3.9.2 移动端项目技术栈

| 技术 | 版本 | 作用 |
|------|:----:|------|
| **Flutter SDK** | 3.2.0 ~ 3.x | 跨平台 UI 框架 |
| **Dart** | 3.2.0+ | Flutter 使用的编程语言 |
| **Riverpod** | 2.4.9 | 状态管理（管理 APP 中的数据流动） |
| **Dio** | 5.4.0 | HTTP 请求库（和 Axios 一样的角色） |
| **Go Router** | 13.0.0 | 页面路由（管理 APP 内页面跳转） |
| **Flutter Map** | 6.1.0 | 地图组件（显示无人机位置） |

#### 3.9.3 Flutter 项目目录结构

```
uav-mobile-app/
├── pubspec.yaml                     # 依赖声明文件（相当于前端的 package.json）
├── lib/
│   ├── main.dart                    # APP 入口
│   ├── app.dart                     # APP 根组件
│   ├── router/                      # 路由配置
│   │   └── app_router.dart
│   ├── screens/                     # 页面
│   │   ├── home_screen.dart         # 首页
│   │   ├── drone_monitor_screen.dart # 无人机监控
│   │   ├── path_planning_screen.dart # 路径规划
│   │   └── settings_screen.dart     # 设置
│   ├── widgets/                     # 可复用组件
│   │   └── drone_status_card.dart
│   ├── providers/                   # Riverpod 状态管理
│   │   └── drone_provider.dart
│   └── services/                    # API 服务
│       └── api_service.dart
├── android/                         # Android 原生配置
├── ios/                             # iOS 原生配置
└── test/                            # 测试文件
```

#### 3.9.4 Flutter 环境搭建完整流程

**第一步：下载 Flutter SDK**

1. 访问：https://docs.flutter.dev/get-started/install/windows
2. 下载 Flutter SDK 压缩包
3. 解压到 `C:\flutter`（不要放在 `C:\Program Files\` 等需要管理员权限的目录）

**第二步：配置环境变量**

```bash
# 将 Flutter 的 bin 目录加入 PATH
# Windows：在系统环境变量 Path 中添加 C:\flutter\bin
```

**第三步：运行 Flutter Doctor（诊断工具）**

```bash
flutter doctor
```

这个命令会检查你的环境是否完整。理想输出应该是所有项前面都是绿色的 `[√]`。

常见需要解决的问题：
- `[!] Android toolchain` → 需要安装 Android Studio
- `[!] Android Studio` → 需要安装 Android Studio 并配置 Android SDK

**第四步：安装 Android Studio（用于 Android 模拟器和 SDK）**

1. 下载：https://developer.android.com/studio
2. 安装后打开，在 SDK Manager 中下载：
   - Android SDK Platform 33
   - Android SDK Build-Tools
   - Android Emulator

#### 3.9.5 编译 Flutter 项目

```bash
# 1. 进入移动端项目目录
cd d:\Developer\workplace\py\iteam\trae\uav-mobile-app

# 2. 获取依赖（首次运行必须）
flutter pub get

# 3. 检查环境
flutter doctor
```

#### 3.9.6 Flutter API 调用示例（连接后端）

```dart
// lib/services/api_service.dart

import 'package:dio/dio.dart';

class ApiService {
  final Dio _dio = Dio(BaseOptions(
    // 【自定义】改成你的后端地址
    baseUrl: 'http://10.0.2.2:8088',  // Android 模拟器中 10.0.2.2 = 宿主机 localhost
    connectTimeout: Duration(seconds: 10),
  ));

  // 用户登录
  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await _dio.post('/v1/auth/login', data: {
      'username': username,
      'password': password,
    });
    return response.data;
  }

  // 获取无人机列表
  Future<List<dynamic>> getDroneList() async {
    final response = await _dio.get('/v1/platform/drones');
    return response.data;
  }

  // 路径规划
  Future<Map<String, dynamic>> planPath(Map<String, dynamic> params) async {
    final response = await _dio.post('/v1/planning/path', data: params);
    return response.data;
  }
}
```

> **关于地址的说明**：
> - Android 模拟器访问宿主机的 localhost → 用 `10.0.2.2`
> - iOS 模拟器访问宿主机的 localhost → 直接用 `localhost`
> - 真机调试 → 用电脑的局域网 IP（如 `192.168.x.x`）

#### 3.9.7 运行 Flutter APP

```bash
# 查看可用的设备
flutter devices

# 方式一：在 Chrome 中运行（Web 模式，最快上手）
flutter run -d chrome

# 方式二：在 Android 模拟器中运行
# 先打开 Android Studio → AVD Manager → 创建并启动一个模拟器
flutter run

# 方式三：真机调试
# 用 USB 连接手机，手机开启"开发者选项"和"USB 调试"
flutter run
```

#### 3.9.8 Flutter 打包发布

```bash
# Android APK 打包
flutter build apk --release
# 生成的 APK 在：build/app/outputs/flutter-apk/app-release.apk

# iOS 打包（需要在 macOS 上执行）
flutter build ios --release

# 确保打包前更新版本号（在 pubspec.yaml 中）
# version: 1.0.0+1
```

---

### 3.10 Python 算法模块开发指南

#### 3.10.1 Python 模块在本项目中的角色

| 模块 | 路径 | 核心算法 |
|------|------|---------|
| **WRF 数据处理** | `wrf-processor/` | WRF 数值天气预报前处理、后处理、可视化 |
| **数据同化平台** | `data-assimilation-platform/algorithm_core/` | 3D-VAR、4D-VAR、EnKF、Hybrid 同化 |
| **路径规划算法** | `path-planning-service/` 调用 | VRPTW、RRT*、DWA、A*、Dijkstra、遗传算法、PSO |

#### 3.10.2 安装 Python 依赖

```bash
cd d:\Developer\workplace\py\iteam\trae

# 安装 WRF 处理器依赖
pip install -r wrf-processor/requirements.txt

# 安装数据同化平台依赖
pip install -r data-assimilation-platform/requirements.txt

# 安装测试依赖
pip install -r tests/requirements.txt
```

#### 3.10.3 运行 WRF 数据处理

```bash
cd d:\Developer\workplace\py\iteam\trae\wrf-processor

# 运行 WRF 前处理（准备气象输入数据）
python preprocess.py

# 运行 WRF 主程序
python run_wrf.py

# 运行 WRF 后处理（提取无人机路径规划所需气象要素）
python postprocess.py
```

---

## 第四章：联调测试 —— 让所有部分一起工作

### 4.1 后端微服务本地联调

#### 4.1.1 启动基础设施（一键 Docker）

```bash
cd d:\Developer\workplace\py\iteam\trae

# 仅启动中间件（不启动微服务）
docker-compose up -d mysql redis nacos kafka

# 等待全部就绪（约 30 秒）
# 验证：
docker-compose ps  # 所有状态应为 Up (healthy)
```

#### 4.1.2 验证中间件可用性

```bash
# 1. 验证 MySQL
mysql -h localhost -P 3306 -u root -p
# 输入密码后执行：
SHOW DATABASES;
# 应看到 uav_platform、wrf_processor 等 6 个数据库

# 2. 验证 Redis
redis-cli -h localhost -p 6379 ping
# 应返回：PONG

# 3. 验证 Nacos
curl http://localhost:8848/nacos/
# 返回 HTML 说明 Nacos 运行正常

# 4. 验证 Kafka
kafka-topics.sh --list --bootstrap-server localhost:9092
# 应正常返回（可能为空列表）
```

#### 4.1.3 启动核心微服务

```bash
# 第 1 个终端：启动 uav-platform-service
cd d:\Developer\workplace\py\iteam\trae
mvn spring-boot:run -pl uav-platform-service

# 第 2 个终端：启动 path-planning-service
cd d:\Developer\workplace\py\iteam\trae
mvn spring-boot:run -pl path-planning-service

# 第 3 个终端：启动 api-gateway
cd d:\Developer\workplace\py\iteam\trae
mvn spring-boot:run -pl api-gateway
```

#### 4.1.4 测试微服务间调用

```bash
# 通过 API Gateway 访问平台服务
curl http://localhost:8088/api/v1/platform/health

# 直接访问平台服务
curl http://localhost:8080/actuator/health

# 在 Nacos 控制台查看服务注册情况
# 打开 http://localhost:8848/nacos → 服务管理 → 服务列表
```

---

### 4.2 前后端接口联调

#### 4.2.1 联调前的检查清单

| 检查项 | 命令/操作 | 期望结果 |
|--------|----------|---------|
| API Gateway 是否运行 | `curl http://localhost:8088/actuator/health` | `{"status":"UP"}` |
| Vue 前端是否启动 | 浏览器打开 http://localhost:3000 | 能看到页面 |
| 代理是否生效 | 浏览器 F12 → Network → 查看请求是否发到 3000 | 状态码非 404 |

#### 4.2.2 登录接口联调（完整流程）

**第 1 步：确认后端登录接口可用**

```bash
curl -X POST http://localhost:8088/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# 预期返回包含 token：
# {"token":"eyJhbGciOiJIUzI1NiJ9...","user":{"id":1,"username":"admin"}}
```

**第 2 步：在前端页面登录**

1. 浏览器打开 http://localhost:3000
2. 输入用户名 `admin`、密码 `password`
3. 点击登录
4. 打开浏览器开发者工具（F12）→ Network 标签 → 找到 `/api/v1/auth/login` 请求 → 查看 Request 和 Response

**第 3 步：用 Token 调用受保护接口**

```bash
# 将 YOUR_TOKEN 替换为上一步拿到的 token
curl http://localhost:8088/v1/platform/drones \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预期返回无人机列表的 JSON 数据
```

#### 4.2.3 常见联调问题速查

| 现象 | 可能原因 | 解决方案 |
|------|---------|---------|
| 前端页面空白 | 前端未启动或端口被占 | 检查 `npm run dev` 是否正常 |
| 接口返回 404 | 路由配置错误 | 检查 API Gateway 路由规则 |
| 接口返回 401 | Token 过期或未传 | 重新登录获取 Token |
| 接口返回 500 | 后端服务内部错误 | 查看后端控制台日志 |
| 跨域报错（CORS） | 代理未配置 | 检查 vite.config.js 的 proxy |
| "Network Error" | 后端未启动 | 检查目标服务是否运行 |

---

### 4.3 Flutter 客户端联调

#### 4.3.1 确保后端服务就绪

```bash
# 确认关键接口可访问
curl http://localhost:8088/v1/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

#### 4.3.2 配置移动端 API 地址

```dart
// lib/services/api_service.dart

class ApiService {
  static String get baseUrl {
    // 【自定义】根据调试方式选择地址
    if (kIsWeb) {
      return 'http://localhost:8088';     // Web 模式
    }
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8088';      // Android 模拟器
    }
    if (Platform.isIOS) {
      return 'http://localhost:8088';      // iOS 模拟器
    }
    // 【自定义】真机调试时改成你电脑的局域网 IP
    return 'http://192.168.1.100:8088';
  }
}
```

#### 4.3.3 运行移动端 APP

```bash
cd d:\Developer\workplace\py\iteam\trae\uav-mobile-app

# 方式一：Web 模式（最快，不需要模拟器）
flutter run -d chrome

# 方式二：Android 模拟器
# 1. 打开 Android Studio → AVD Manager → 启动模拟器
# 2. 在模拟器中运行
flutter run

# 方式三：真机 USB 调试
# 1. 手机开启开发者选项和 USB 调试
# 2. USB 连接电脑
# 3. 手机授权电脑调试
flutter devices  # 应能看到你的手机
flutter run
```

---

### 4.4 功能测试思路与测试用例设计

#### 4.4.1 测试是什么？为什么需要？

测试就是"验证程序是否按预期工作"。比如你写了一个"1+1"的计算器，测试就是验证它是否真的输出 `2` 而不是 `3`。

#### 4.4.2 本项目测试分层

| 测试类型 | 测试范围 | 工具 | 执行方式 |
|----------|---------|------|---------|
| **单元测试** | 单个方法/类 | JUnit 5 + Mockito | `mvn test` |
| **接口测试** | 单个 HTTP 接口 | Postman / curl | 手动发送请求 |
| **集成测试** | 多个服务协作 | SpringBoot Test + TestRestTemplate | `mvn verify` |

#### 4.4.3 测试用例设计模板

以"用户登录"功能为例：

| 用例编号 | 测试场景 | 输入 | 预期输出 |
|:-------:|---------|------|---------|
| TC-001 | 正常登录 | 用户名: admin, 密码: password | 返回 token，状态码 200 |
| TC-002 | 密码错误 | 用户名: admin, 密码: wrong | 返回错误信息，状态码 401 |
| TC-003 | 用户名不存在 | 用户名: nobody, 密码: xxx | 返回错误信息，状态码 401 |
| TC-004 | 空用户名 | 用户名: "", 密码: xxx | 返回参数校验失败，状态码 400 |
| TC-005 | 超长密码 | 用户名: admin, 密码: (500字符) | 返回参数校验失败，状态码 400 |

#### 4.4.4 执行单元测试

```bash
# 运行所有模块的测试
mvn test

# 只运行指定模块的测试
mvn test -pl uav-platform-service

# 跳过测试（快速构建时）
mvn package -DskipTests
```

---

### 4.5 接口测试执行方案

#### 4.5.1 使用 curl 进行快速接口测试

```bash
# 1. 健康检查（所有服务通用）
curl http://localhost:8088/actuator/health
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health

# 2. 登录获取 Token
TOKEN=$(curl -s -X POST http://localhost:8088/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' | grep -o '"token":"[^"]*' | cut -d'"' -f4)

# 3. 携带 Token 调用受保护接口
curl http://localhost:8088/v1/platform/drones \
  -H "Authorization: Bearer $TOKEN"

# 4. 提交路径规划请求
curl -X POST http://localhost:8088/v1/planning/path \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "startLat": 31.2304,
    "startLon": 121.4737,
    "endLat": 31.2500,
    "endLon": 121.5000,
    "droneSpeed": 15.0,
    "maxFlightTime": 30
  }'
```

#### 4.5.2 关键接口测试清单

| 序号 | 服务 | 接口 | 方法 | 测试重点 |
|:----:|------|------|:----:|---------|
| 1 | platform-service | `/api/v1/auth/login` | POST | 正常登录、密码错误、Token 过期 |
| 2 | platform-service | `/api/v1/platform/drones` | GET | 分页查询、搜索过滤、空列表 |
| 3 | platform-service | `/api/v1/platform/tasks` | POST | 创建任务、必填字段校验 |
| 4 | wrf-processor | `/api/wrf/process` | POST | WRF 数据提交、格式校验 |
| 5 | path-planning | `/api/planning/path` | POST | 路径生成、异常坐标处理 |
| 6 | meteor-forecast | `/api/forecast/predict` | POST | 预测结果格式、超时处理 |

> 完整的 API 文档请参阅：[api/API_DOCUMENTATION.md](./api/API_DOCUMENTATION.md)

---

## 第五章：容器部署 —— 打包发布上线

### 5.1 Docker 镜像构建与多阶段打包

#### 5.1.1 多阶段构建是什么？

Docker 多阶段构建可以理解为"先在一个房间里组装，只把成品搬到另一个房间"。第一阶段用 Maven 编译打包 Java 代码（这个阶段环境很重），第二阶段只把编好的 jar 包放进一个干净的轻量环境运行。

#### 5.1.2 项目中的 Dockerfile 示例（api-gateway）

```dockerfile
# ===== 阶段一：构建阶段 =====
# 用 Maven + JDK 17 编译打包
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /app
# 先复制 POM 文件，利用 Docker 缓存加速
COPY pom.xml .
COPY common-dependencies/pom.xml common-dependencies/
COPY common-utils/pom.xml common-utils/
COPY api-gateway/pom.xml api-gateway/

# 下载依赖（这一层会被缓存，改代码不会重新下载依赖）
RUN mvn dependency:go-offline -pl api-gateway -am

# 复制源代码并编译
COPY common-dependencies/src common-dependencies/src/
COPY common-utils/src common-utils/src/
COPY api-gateway/src api-gateway/src/
RUN mvn clean package -pl api-gateway -am -DskipTests

# ===== 阶段二：运行阶段 =====
# 用精简的 JRE 17 镜像运行
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app
# 从构建阶段复制 jar 包
COPY --from=builder /app/api-gateway/target/*.jar app.jar

# 暴露端口
EXPOSE 8088

# 启动命令
ENTRYPOINT ["java", "-jar", "app.jar"]
```

> **多阶段构建的好处**：最终镜像只有约 200MB（只有 JRE + jar），而如果用 Maven 镜像直接运行会有 600MB+。

#### 5.1.3 构建单个服务的镜像

```bash
# 构建 api-gateway 镜像
cd d:\Developer\workplace\py\iteam\trae
docker build -t uav/api-gateway:latest -f api-gateway/Dockerfile .

# 验证镜像
docker images uav/api-gateway
```

---

### 5.2 Docker Compose 服务编排

#### 5.2.1 什么是 Docker Compose？

想象你要同时启动 10 台设备：MySQL、Redis、Nacos、Kafka + 6 个微服务。如果一条一条输入 `docker run`，不仅累还容易出错。Docker Compose 就是"一键启动脚本"，把所有服务的配置写在一个 YAML 文件里，一条命令全部搞定。

#### 5.2.2 项目 docker-compose.yml 核心结构

本项目的 `docker-compose.yml` 已在项目根目录，以下讲解其关键配置：

```yaml
# docker-compose.yml —— 服务编排主文件

services:
  # ===== 基础设施层 =====
  mysql:
    image: mysql:8.0
    container_name: uav-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}      # 【自定义】通过 .env 文件设置
      MYSQL_DATABASE: uav_platform
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql               # 数据持久化
    healthcheck:                                 # 健康检查
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      retries: 5

  redis:
    image: redis:6.2-alpine
    container_name: uav-redis
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      retries: 5

  nacos:
    image: nacos/nacos-server:v2.3.0
    container_name: uav-nacos
    environment:
      - MODE=standalone          # 单机模式（开发/测试用）
      - JVM_XMS=256m             # JVM 最小内存
      - JVM_XMX=512m             # JVM 最大内存
    ports:
      - "8848:8848"

  kafka:
    image: bitnami/kafka:3.6
    container_name: uav-kafka
    environment:
      - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
    ports:
      - "9092:9092"

  # ===== 微服务层 =====
  api-gateway:
    build:
      context: .
      dockerfile: api-gateway/Dockerfile
    container_name: uav-api-gateway
    ports:
      - "8088:8088"
    depends_on:              # 依赖关系：等 nacos 启动后再启动
      nacos:
        condition: service_healthy
    environment:
      - NACOS_SERVER=nacos:8848
    networks:
      - uav-network

  uav-platform-service:
    build:
      context: .
      dockerfile: uav-platform-service/Dockerfile
    container_name: uav-platform
    ports:
      - "8080:8080"
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DB_HOST=mysql        # 【注意】容器内用容器名，不是 localhost
      - DB_PORT=3306
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - NACOS_SERVER=nacos:8848
    networks:
      - uav-network

networks:
  uav-network:
    driver: bridge

volumes:
  mysql-data:
  redis-data:
```

> **关键理解**：容器之间通信用**容器名**（如 `mysql`、`redis`、`nacos`），而不是 `localhost`。因为在 Docker 网络中，每个容器都有自己的"主机名"。

---

### 5.3 一键部署完整流程

#### 5.3.1 第 1 步：配置环境变量

```bash
cd d:\Developer\workplace\py\iteam\trae

# 复制环境变量模板
copy .env.example .env

# 编辑 .env 文件（用记事本或 VS Code 打开）
# 【自定义】至少修改以下三项：
#   DB_PASSWORD=你的数据库密码（不能是 123456）
#   JWT_SECRET=你的 JWT 密钥（至少 32 位随机字符串）
#   ENCRYPTION_KEY=你的加密密钥
```

`.env` 文件模板：

```ini
# ===== 数据库 =====
DB_HOST=mysql
DB_PORT=3306
DB_PASSWORD=your_secure_password_here

# ===== JWT 认证 =====
JWT_SECRET=your_jwt_secret_at_least_32_characters_long
JWT_EXPIRATION=86400000

# ===== Nacos =====
NACOS_SERVER=nacos:8848

# ===== Redis =====
REDIS_HOST=redis
REDIS_PORT=6379

# ===== Kafka =====
KAFKA_SERVER=kafka:9092
```

#### 5.3.2 第 2 步：构建并启动所有服务

```bash
# 在项目根目录执行
docker-compose up -d --build

# 参数说明：
#   up     - 启动所有服务
#   -d     - 后台运行（detached mode）
#   --build - 启动前重新构建镜像（首次或代码改动后必须加）
```

#### 5.3.3 第 3 步：查看启动状态

```bash
# 查看所有容器状态
docker-compose ps

# 预期：所有服务的 STATUS 列显示 "Up (healthy)"

# 查看实时日志
docker-compose logs -f

# 只看某个服务的日志
docker-compose logs -f api-gateway
```

#### 5.3.4 第 4 步：验证部署成功

```bash
# 1. 验证 API Gateway
curl http://localhost:8088/actuator/health
# 预期：{"status":"UP"}

# 2. 验证 Nacos 控制台
# 浏览器打开 http://localhost:8848/nacos
# 服务列表中应看到所有微服务

# 3. 验证登录接口
curl -X POST http://localhost:8088/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

#### 5.3.5 常用 Docker Compose 命令

| 命令 | 作用 |
|------|------|
| `docker-compose up -d` | 启动所有服务（后台运行） |
| `docker-compose up -d --build` | 重新构建镜像并启动 |
| `docker-compose down` | 停止并删除所有容器 |
| `docker-compose down -v` | 停止并删除所有容器+数据卷（⚠谨慎） |
| `docker-compose restart` | 重启所有服务 |
| `docker-compose restart api-gateway` | 只重启某个服务 |
| `docker-compose ps` | 查看所有容器状态 |
| `docker-compose logs -f` | 查看实时日志 |
| `docker-compose logs -f --tail=100` | 查看最近 100 行日志 |
| `docker-compose pull` | 拉取最新镜像（不重新构建） |

---

### 5.4 生产环境服务器准备与域名配置

#### 5.4.1 服务器最低配置要求

| 资源 | 最低要求 | 推荐配置 |
|------|:-------:|:-------:|
| **CPU** | 4 核 | 8 核 |
| **内存** | 8 GB | 16 GB |
| **磁盘** | 50 GB SSD | 100 GB SSD |
| **操作系统** | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| **带宽** | 10 Mbps | 100 Mbps |

> **说明**：本项目启动全套服务约占用 4~6 GB 内存。8 GB 服务器勉强够用，16 GB 更从容。

#### 5.4.2 服务器初始化步骤

```bash
# 1. 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 2. 安装 Docker（使用官方脚本）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# 重新登录使 docker 组生效

# 3. 安装 Git
sudo apt-get install -y git

# 4. 拉取项目
git clone https://github.com/602420232-dotcom/weather.git
cd trae

# 5. 配置 .env（生产环境密钥务必使用强密码！）
cp .env.example .env
nano .env  # 编辑环境变量

# 6. 启动服务
docker-compose up -d --build
```

#### 5.4.3 端口规划与防火墙配置

```bash
# 对外开放的端口（使用 ufw 防火墙）
sudo ufw allow 80/tcp      # HTTP（前端 Nginx）
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 22/tcp      # SSH（远程管理）

# 以下端口仅在服务器内部使用，不对公网开放
# 8080-8094  微服务端口
# 3306       MySQL
# 6379       Redis
# 8848       Nacos
# 9092       Kafka

# 启用防火墙
sudo ufw enable
sudo ufw status
```

#### 5.4.4 域名与 HTTPS 配置（Nginx 反向代理）

```nginx
# /etc/nginx/sites-available/uav-platform

server {
    listen 80;
    # 【自定义】改成你的域名
    server_name uav.example.com;

    # 前端静态资源
    location / {
        root /var/www/uav-frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理到 API Gateway
    location /api/ {
        proxy_pass http://127.0.0.1:8088/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理（边云协同用）
    location /ws/ {
        proxy_pass http://127.0.0.1:8765/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用 HTTPS（使用 Certbot 自动获取 Let's Encrypt 免费证书）：

```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 自动配置 HTTPS
sudo certbot --nginx -d uav.example.com

# 测试自动续期
sudo certbot renew --dry-run
```

#### 5.4.5 生产环境检查清单

| 检查项 | 命令/操作 | 通过标准 |
|--------|----------|---------|
| Docker 服务运行 | `docker-compose ps` | 所有服务 Up |
| 网关健康检查 | `curl localhost:8088/actuator/health` | `{"status":"UP"}` |
| Nacos 可访问 | 浏览器打开 8848/nacos | 能看到控制台 |
| MySQL 连接正常 | `mysql -h localhost -u uav -p` | 能登录并查询 |
| 前端页面可访问 | 浏览器打开域名 | 页面正常加载 |
| HTTPS 生效 | 浏览器打开 https://域名 | 显示安全锁图标 |
| 防火墙配置 | `sudo ufw status` | 只开放必要端口 |
| 磁盘空间 | `df -h` | 使用率 < 80% |
| 内存使用 | `free -h` | 可用 > 2GB |

---

## 第六章：运维排障 —— 出了问题怎么办

### 6.1 日常维护清单

#### 6.1.1 每天检查（约 5 分钟）

```bash
# 1. 所有容器是否正常运行
docker-compose ps
# 确保没有 STATUS 为 "Restarting" 或 "Exited" 的容器

# 2. 查看各服务日志（最近 50 行）
docker-compose logs --tail=50 api-gateway
docker-compose logs --tail=50 uav-platform-service

# 3. 检查磁盘使用率
df -h
# 确保 /var/lib/docker 分区使用率 < 80%
```

#### 6.1.2 每周检查（约 15 分钟）

```bash
# 1. 清理无用的 Docker 资源（释放磁盘空间）
docker system prune -f

# 2. 查看 MySQL 慢查询日志
docker exec uav-mysql mysql -u root -p -e "SHOW VARIABLES LIKE 'slow_query%';"

# 3. 备份数据库
docker exec uav-mysql mysqldump -u root -p --all-databases > backup_$(date +%Y%m%d).sql

# 4. 检查 Nacos 配置是否有异常
# 浏览器打开 Nacos 控制台 → 配置管理 → 配置列表 → 检查历史变更
```

#### 6.1.3 每月检查（约 30 分钟）

```bash
# 1. 更新 Docker 镜像
docker-compose pull
docker-compose up -d --build

# 2. 检查 JVM 内存使用
docker stats --no-stream

# 3. 清理过期日志（保留最近 30 天）
find /var/lib/docker/containers -name "*.log" -mtime +30 -delete

# 4. 安全审计
# - 检查 .env 中的密钥是否定期更换
# - 检查 Nacos 控制台是否有未知服务注册
# - 检查 MySQL 是否有异常登录
```

---

### 6.2 常见报错原因分析与解决方案

#### 问题 1：端口被占用

**现象**：启动服务时报错 `Port 8080 was already in use` 或 `bind: address already in use`

**原因**：另一个程序（或之前未正常关闭的服务实例）占用了该端口

**解决方案**：

```bash
# Windows：查找占用端口的进程
netstat -ano | findstr :8080
# 记下最后一列的 PID（进程 ID）
taskkill /PID 占用的PID /F

# Linux/Mac：
lsof -i :8080
kill -9 占用的PID
```

---

#### 问题 2：MySQL 连接失败

**现象**：启动报错 `CommunicationsException: Communications link failure` 或 `Access denied for user 'uav'`

**原因**：
- MySQL 服务未启动
- 用户名或密码错误
- 数据库不存在

**解决方案**：

```bash
# 第 1 步：确认 MySQL 是否运行
docker ps | grep mysql

# 第 2 步：进入 MySQL 容器检查
docker exec -it uav-mysql mysql -u root -p

# 第 3 步：检查数据库是否存在
SHOW DATABASES;

# 第 4 步：检查用户权限
SELECT user, host FROM mysql.user WHERE user = 'uav';

# 第 5 步：如果数据库不存在，重新创建
CREATE DATABASE IF NOT EXISTS uav_platform DEFAULT CHARACTER SET utf8mb4;
GRANT ALL PRIVILEGES ON uav_platform.* TO 'uav'@'%';
FLUSH PRIVILEGES;
```

---

#### 问题 3：Maven 依赖下载失败

**现象**：`mvn clean install` 时报 `Could not transfer artifact` 或 `Connection timed out`

**原因**：
- 网络问题
- Maven 镜像源未配置或配置错误
- 本地仓库缓存损坏

**解决方案**：

```bash
# 第 1 步：确认镜像源配置正确（见第一章 1.3 节）
# 检查 C:\Users\你的用户名\.m2\settings.xml 是否存在且配置正确

# 第 2 步：清理本地缓存
rmdir /s /q %USERPROFILE%\.m2\repository  # Windows
rm -rf ~/.m2/repository                     # Mac/Linux

# 第 3 步：强制重新下载
mvn clean install -U -DskipTests
```

> 详细排查请参阅：[MAVEN_FIX.md](./MAVEN_FIX.md)

---

#### 问题 4：Nacos 连接失败

**现象**：微服务日志中出现 `com.alibaba.nacos.api.exception.NacosException: failed to req API`

**原因**：
- Nacos 服务未启动
- bootstrap.yml 中 Nacos 地址配置错误
- 防火墙阻止 8848 端口

**解决方案**：

```bash
# 第 1 步：确认 Nacos 是否运行
curl http://localhost:8848/nacos/

# 第 2 步：如果未运行，启动 Nacos
docker-compose up -d nacos

# 第 3 步：检查微服务的 bootstrap.yml 配置
# server-addr 必须是 localhost:8848（本地）或 nacos:8848（Docker 内）
```

---

#### 问题 5：Redis 连接失败

**现象**：`Cannot connect to Redis; nested exception is io.lettuce.core.RedisConnectionException`

**原因**：Redis 服务未启动或配置的地址不对

**解决方案**：

```bash
# 第 1 步：确认 Redis 是否运行
docker-compose ps redis

# 第 2 步：测试连接
redis-cli -h localhost -p 6379 ping
# 或 Docker 方式：
docker exec uav-redis redis-cli ping

# 第 3 步：如果未运行
docker-compose up -d redis
```

---

#### 问题 6：Docker 容器反复重启

**现象**：`docker-compose ps` 显示容器 STATUS 为 `Restarting`

**原因**：容器内的应用启动失败

**解决方案**：

```bash
# 第 1 步：查看容器日志（找到真正的报错）
docker-compose logs --tail=100 容器名称

# 第 2 步：常见原因
# - Java 内存不足 → 在 docker-compose.yml 中增加 JVM 参数
# - 数据库连接不上 → 确认 depends_on 和 healthcheck 配置正确
# - 配置文件错误 → 进入容器检查 /app/application.yml
docker exec -it 容器名称 cat /app/application.yml

# 第 3 步：手动进入容器调试
docker exec -it 容器名称 /bin/sh
```

---

#### 问题 7：前端页面加载空白

**现象**：浏览器打开 http://localhost:3000 页面一片空白

**解决方案**：

```bash
# 第 1 步：确认开发服务器是否正常运行
# 终端中能看到 "VITE v5.0.0  ready" 的输出

# 第 2 步：检查浏览器控制台（F12 → Console）
# 看是否有红色报错信息

# 第 3 步：检查 Network 标签（F12 → Network）
# 确认 API 请求是否发出，返回什么状态码

# 第 4 步：清除 node_modules 重新安装
cd d:\Developer\workplace\py\iteam\trae\uav-path-planning-system\frontend-vue
rm -rf node_modules
npm install
npm run dev
```

---

#### 问题 8：Flutter APP 闪退或白屏

**现象**：APP 启动后立即闪退或长时间显示白屏

**解决方案**：

```bash
# 第 1 步：清理构建缓存
cd d:\Developer\workplace\py\iteam\trae\uav-mobile-app
flutter clean
flutter pub get

# 第 2 步：检查环境
flutter doctor -v

# 第 3 步：在 debug 模式运行（查看详细日志）
flutter run --debug

# 第 4 步：检查 API 地址是否正确
# 确认 lib/services/api_service.dart 中的 baseUrl 配置
```

#### 问题速查表（一图定位所有问题）

| 症状 | 最快诊断命令 | 最可能原因 | 解决方案 |
|------|------------|-----------|---------|
| 端口冲突 | `netstat -ano \| findstr :8080` | 上次服务未关闭 | `taskkill /PID xxx /F` |
| Maven 报红 | `mvn -v` | Maven 未配/版本不对 | 检查 MAVEN_HOME 和镜像源 |
| 数据库连不上 | `mysql -u root -p` | MySQL 未启动/密码错 | `docker-compose up -d mysql` |
| Nacos 拒绝连接 | `curl localhost:8848` | Nacos 未启动 | `docker-compose up -d nacos` |
| Redis 报错 | `redis-cli ping` | Redis 未启动 | `docker-compose up -d redis` |
| 容器反复重启 | `docker-compose logs 容器名` | 应用启动报错 | 查看日志定位根因 |
| 前端空白 | F12 → Console | JS 报错/接口不通 | 修复报错后刷新 |
| Flutter 白屏 | `flutter clean && flutter run` | 缓存问题/API 不通 | 清理后重试 |

---

### 6.3 应急操作手册

#### 紧急重启某个服务

```bash
# 方式一：Docker Compose 重启
docker-compose restart api-gateway

# 方式二：停止再启动（更彻底）
docker-compose stop api-gateway
docker-compose up -d api-gateway

# 方式三：完全重建（配置或镜像变动后）
docker-compose up -d --build --force-recreate api-gateway
```

#### 紧急回滚

```bash
# 查看最近的部署记录
docker-compose logs --tail=50

# 如果有数据库变更，恢复备份
docker exec -i uav-mysql mysql -u root -p < backup_20260514.sql

# 停止当前服务
docker-compose down

# 切换回旧版本代码
git checkout <之前的commit-hash>

# 重新构建并启动
docker-compose up -d --build
```

#### 紧急扩容（资源不足时）

临时释放磁盘空间：

```bash
# 清理停止的容器
docker container prune -f

# 清理未使用的镜像
docker image prune -a -f

# 清理未使用的卷
docker volume prune -f

# 一键清理（谨慎！会删除所有未使用的 Docker 资源）
docker system prune -a -f
```

---

## 附录：专题文档索引

本总指南配套以下专题文档，存放在 `docs/` 目录下。当你需要深入了解某个特定主题时，可以通过链接跳转查看：

### 架构与设计

| 文档 | 路径 | 说明 |
|------|------|------|
| **架构设计文档** | [architecture.md](./architecture.md) | 微服务分层架构、模块边界定义、架构决策记录 |
| **项目结构指南** | [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | 完整目录树、各子模块文件清单 |
| **端口配置总表** | [PORTS_CONFIGURATION.md](./PORTS_CONFIGURATION.md) | 所有服务端口、路由映射、端口分配原则 |
| **数据同化平台** | [data_assimilation_platform.md](./data_assimilation_platform.md) | 贝叶斯数据同化算法平台详解 |
| **API 聚合配置** | [API_AGGREGATION_CONFIG.md](./API_AGGREGATION_CONFIG.md) | API 聚合优化配置 |

### 部署与运维

| 文档 | 路径 | 说明 |
|------|------|------|
| **Docker 部署指南** | [DOCKER.md](./DOCKER.md) | Docker 镜像构建、端口映射、快速启动 |
| **部署与维护方案** | [deployment/DEPLOYMENT.md](./deployment/DEPLOYMENT.md) | Docker Compose + K8s 完整部署方案 |
| **详细部署指南** | [deployment/DEPLOY_GUIDE.md](./deployment/DEPLOY_GUIDE.md) | 环境要求、架构总览、分布部署 |
| **灾难恢复计划** | [deployment/DISASTER_RECOVERY_PLAN.md](./deployment/DISASTER_RECOVERY_PLAN.md) | 数据备份、故障恢复流程 |

### 开发指南

| 文档 | 路径 | 说明 |
|------|------|------|
| **Maven 依赖修复** | [MAVEN_FIX.md](./MAVEN_FIX.md) | Maven 依赖下载问题排查与修复 |
| **快速参考卡** | [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) | 常用命令速查、API 端点 |
| **API 完整文档** | [api/API_DOCUMENTATION.md](./api/API_DOCUMENTATION.md) | 所有接口定义、请求响应示例 |
| **Feign 迁移指南** | [FEIGN_MIGRATION_GUIDE.md](./FEIGN_MIGRATION_GUIDE.md) | OpenFeign 迁移说明 |

### 专项指南

| 文档 | 路径 | 说明 |
|------|------|------|
| **熔断器使用指南** | [guides/CIRCUIT_BREAKER_GUIDE.md](./guides/CIRCUIT_BREAKER_GUIDE.md) | Resilience4j 熔断器配置与使用 |
| **熔断器使用示例** | [guides/CIRCUIT_BREAKER_USAGE_EXAMPLES.md](./guides/CIRCUIT_BREAKER_USAGE_EXAMPLES.md) | 熔断器实战代码示例 |
| **异常 HTTP 状态码** | [guides/EXCEPTION_HTTP_STATUS_GUIDE.md](./guides/EXCEPTION_HTTP_STATUS_GUIDE.md) | 异常与 HTTP 状态码映射规范 |
| **生产环境密钥指南** | [guides/PRODUCTION_SECRETS_GUIDE.md](./guides/PRODUCTION_SECRETS_GUIDE.md) | JWT、加密密钥等安全配置规范 |
| **问题排查指南** | [guides/TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md) | 常见问题与解决方案 |

### API 专项文档

| 服务 | 路径 |
|------|------|
| **uav-platform-service** | [api/uav-platform-service/README.md](./api/uav-platform-service/README.md) |
| **wrf-processor-service** | [api/wrf-processor-service/README.md](./api/wrf-processor-service/README.md) |
| **meteor-forecast-service** | [api/meteor-forecast-service/README.md](./api/meteor-forecast-service/README.md) |
| **path-planning-service** | [api/path-planning-service/README.md](./api/path-planning-service/README.md) |
| **data-assimilation-service** | [api/data-assimilation-service/README.md](./api/data-assimilation-service/README.md) |
| **uav-weather-collector** | [api/uav-weather-collector/README.md](./api/uav-weather-collector/README.md) |
| **edge-cloud-coordinator** | [api/edge-cloud-coordinator/README.md](./api/edge-cloud-coordinator/README.md) |
| **backend-spring** | [api/uav-path-planning-system/README.md](./api/uav-path-planning-system/README.md) |

### 补充学习资源索引

| 主题 | 说明 | 在本文档中的位置 |
|------|------|-----------------|
| **Java 17 基础** | 类与对象、注解、数据结构速成 | [3.1 节](#31-java-17-必备基础知识点) |
| **SpringBoot 微服务** | 分层架构、配置、启动流程 | [3.2 节](#32-springboot-微服务核心架构原理) |
| **Maven 多模块** | 父 POM、聚合构建、常用命令 | [3.3 节](#33-maven-依赖管理与多模块配置详解) |
| **后端开发实战** | 微服务启动、数据库配置、Nacos 接入 | [3.4~3.7 节](#34-后端微服务模块开发实战) |
| **Vue 前端开发** | 项目结构、组件、接口调用、代理配置 | [3.8 节](#38-vue-前端项目开发指南) |
| **Flutter 移动端** | 环境搭建、编译、调试、打包 | [3.9 节](#39-flutter-移动端开发指南) |
| **联调测试** | 微服务联调、前后端联调、接口测试 | [第四章](#第四章联调测试--让所有部分一起工作) |
| **Docker 容器化** | 多阶段构建、Compose 编排、一键部署 | [第五章](#第五章容器部署--打包发布上线) |
| **运维排障** | 日常维护、常见问题、应急操作 | [第六章](#第六章运维排障--出了问题怎么办) |

---

> **恭喜你读到这里！** 你已经学习了从环境搭建到生产部署的全流程知识。如果还有不理解的，可以回到对应章节重新阅读，或者查看附录中的专题文档获取更深入的内容。
>
> **文档版本**：v1.0  
> **最后更新**：2026-05-14  
> **维护者**：DITHIOTHREITOL  
>
> 如有问题或建议，欢迎提交 Issue 或 Pull Request。