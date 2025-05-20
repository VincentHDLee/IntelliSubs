# 为 智字幕 (IntelliSubs) 做出贡献

首先，感谢您考虑为智字幕 (IntelliSubs) 项目做出贡献！我们非常欢迎各种形式的帮助，无论是报告BUG、提出功能建议、改进文档还是直接贡献代码。

## 如何贡献

### 报告问题 (Issues)

*   如果您在使用过程中发现了BUG，或者有任何功能建议，请通过项目的 [GitHub Issues](https://github.com/VincentHDLee/IntelliSubs/issues) 页面提交。
*   在提交BUG报告时，请尽可能提供以下信息：
    *   清晰的标题和描述。
    *   重现BUG的步骤。
    *   期望的结果和实际发生的结果。
    *   您的操作系统版本、IntelliSubs软件版本。
    *   相关的错误截图或日志文件 (如果适用)。
*   在提交功能建议时，请清楚地描述您希望实现的功能以及它为什么对用户有价值。

### 贡献代码

1.  **Fork 本仓库:** 点击仓库右上角的 "Fork" 按钮。
2.  **Clone您的Fork:** `git clone https://github.com/YOUR_USERNAME/IntelliSubs.git`
3.  **创建特性分支:** `git checkout -b feature/your-feature-name` 或 `fix/your-bug-fix-name`
4.  **设置开发环境:**
    *   确保您已安装 Python 3.9+。
    *   建议使用虚拟环境:
        ```bash
        python -m venv venv
        source venv/bin/activate  # Linux/macOS
        venv\Scripts\activate    # Windows
        ```
    *   安装依赖: `pip install -r requirements.txt` (待创建)
    *   详细步骤请参考 [`docs/developer_guide/setup_env.md`](docs/developer_guide/setup_env.md) (待创建)。
5.  **进行代码修改:** 请遵循 [`docs/developer_guide/coding_standards.md`](docs/developer_guide/coding_standards.md) (待创建) 中的编码规范。
6.  **添加测试:** 为您的新功能或修复的BUG编写相应的单元测试或集成测试。
7.  **运行测试:** 确保所有测试通过。
8.  **提交您的更改:**
    *   使用清晰且符合规范的提交信息 (例如，遵循 Conventional Commits)。
    *   `git add .`
    *   `git commit -m "feat: Add new amazing feature"` 或 `fix: Resolve critical bug #123"`
9.  **推送到您的Fork:** `git push origin feature/your-feature-name`
10. **创建Pull Request (PR):** 返回到原始的 `VincentHDLee/IntelliSubs` 仓库页面，您会看到一个提示，可以基于您推送的分支创建一个新的Pull Request。
    *   在PR描述中清晰地说明您所做的更改和解决的问题。
    *   如果您的PR解决了某个已有的Issue, 请在描述中添加 `Closes #issue_number`。

### 改进文档

文档与代码同样重要！如果您发现文档中有任何错误、遗漏或可以改进的地方，欢迎提交PR进行修正。文档文件主要位于根目录和 `docs/` 目录下。

## 行为准则 (Code of Conduct)

为了营造一个开放和友好的环境，我们期望所有贡献者和参与者都能遵守我们的行为准则。请在参与项目活动前阅读 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) (待创建)。

感谢您的贡献！