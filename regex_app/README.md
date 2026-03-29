# 正则表达式的具体应用：物流地址智能解析系统 (Logistics Information Parser)

## 1. 项目背景 (Background)
在物流行业（如顺丰快递、菜鸟裹裹），用户输入的收货信息通常是杂乱无章的字符串。为了实现自动化分拣和下单，系统必须从一段非结构化的文本中准确提取出 **姓名 (Name)**、**电话 (Phone Number)** 和 **详细地址 (Address)**。

本项目利用 **正则表达式 (Regular Expressions)** 实现了这一功能，展示了编译原理中 **词法分析 (Lexical Analysis)** 的核心思想。

## 2. 核心原理 (Core Principles)
本系统的实现逻辑类似于编译器中的词法分析器 (Lexer)：

1.  **扫描 (Scanning)**: 系统读取整个输入文本。
2.  **模式匹配 (Pattern Matching)**: 使用预定义的正则表达式模式来识别特定的 "词法单元 (Tokens)"。
    *   `PHONE_PATTERN`: 识别中国大陆手机号。
    *   `ADDRESS_PATTERN`: 通过 "省/市/区" 等关键词作为锚点进行层次化识别。
    *   `NAME_PATTERN`: 在排除掉地址和电话后，识别剩余的符合姓名特征的汉字词。
3.  **结果输出 (Tokenization)**: 将识别出的数据转换为结构化的 JSON 格式，类似于编译器将源代码转换为 Token 序列。

## 3. 运行指南 (How to Run)
1. 确保安装了 Python 3。
2. 在终端运行：
   ```bash
   python3 parser.py
   ```

## 4. 关键技术点 (Technical Highlights)
*   **非捕获分组 (Non-capturing groups)**: 用于前缀匹配而不计入结果（如 `(?:\+?86)`）。
*   **命名捕获组 (Named Capture Groups)**: 在地址提取中，直接通过 `(?P<province>...)` 将匹配项命名，方便后续提取。
*   **贪婪与非贪婪 (Greedy vs Non-greedy)**: 在提取详细地址时，利用正则的匹配机制确保覆盖所有必要信息。
