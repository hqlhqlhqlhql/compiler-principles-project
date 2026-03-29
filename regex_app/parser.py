import json
from regex_patterns import extract_info

def main():
    test_cases = [
        "张三，13812345678，广东省深圳市南山区软件园101号",
        "15988887777 李四 北京市海淀区清华园1号",
        "王五 四川省成都市武侯区高新区某写字楼 18600001111",
        "新疆维吾尔自治区乌鲁木齐市天山区光明路5号 阿里木 13322223333",
    ]

    print("=== Logistics Information Parser (Lexical Analysis Approach) ===")
    print(f"{'Input Text':<50} | {'Parsed Result'}")
    print("-" * 100)

    for case in test_cases:
        parsed_data = extract_info(case)
        # Clean up None values for display
        display_data = {k: v for k, v in parsed_data.items() if v}
        print(f"{case[:45] + '...':<50} | {json.dumps(display_data, ensure_ascii=False)}")

if __name__ == "__main__":
    main()
