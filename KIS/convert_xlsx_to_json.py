import pandas as pd
import json
import os

def process_kis_excel(file_path, output_dir="./sheets"):
    # Create the root output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Loading Excel file: {file_path} ...")
    xls = pd.ExcelFile(file_path)

    for sheet_name in xls.sheet_names:
        
        # =====================================================================
        # Parse the Master Index Sheet ("API 목록")
        # =====================================================================
        if "API 목록" in sheet_name:
            print(f"Processing index sheet: {sheet_name}")
            df_index = pd.read_excel(xls, sheet_name=sheet_name)
            df_index = df_index.fillna("")
            api_list_data = df_index.to_dict(orient="records")
            
            # Save the master index JSON in the root directory
            output_file = os.path.join(output_dir, "API_목록.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(api_list_data, f, ensure_ascii=False, indent=4)
            continue
        # =====================================================================

        print(f"Processing sheet: {sheet_name}")
        
        # Read the sheet without headers to parse dynamically
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        # Initialize the structured JSON dictionary
        api_data = {
            "category": "",  # <--- Added to capture the Menu Location
            "api_name": "",
            "api_id": "",
            "tr_id_real": "",
            "tr_id_mock": "",
            "endpoint": {
                "method": "",
                "real_domain": "",
                "mock_domain": "",
                "path": ""
            },
            "description": "",
            "request": {
                "headers": [],
                "query_parameters": [],
                "body": []
            },
            "response": {
                "headers": [],
                "body": []
            },
            "examples": {
                "request": "",
                "response": ""
            }
        }

        parsing_layout = False
        current_category = ""

        # Iterate through every row in the sheet
        for idx, row in df.iterrows():
            col_a = str(row[0]).strip() if pd.notna(row[0]) else ""
            col_b = str(row[1]).strip() if pd.notna(row[1]) else ""

            # 1. Extract Metadata
            if col_a == "메뉴 위치": api_data["category"] = col_b  # <--- Extracting Category
            elif col_a == "API 명": api_data["api_name"] = col_b
            elif col_a == "API ID": api_data["api_id"] = col_b
            elif col_a == "실전 TR_ID": api_data["tr_id_real"] = col_b
            elif col_a == "모의 TR_ID": api_data["tr_id_mock"] = col_b
            elif col_a == "HTTP Method": api_data["endpoint"]["method"] = col_b
            elif col_a == "URL 명": api_data["endpoint"]["path"] = col_b
            elif col_a == "실전 Domain": api_data["endpoint"]["real_domain"] = col_b
            elif col_a == "모의 Domain": api_data["endpoint"]["mock_domain"] = col_b
            elif col_a == "개요" and pd.notna(row[1]):
                api_data["description"] = col_b

            # 2. Detect the start of the Layout (Parameters) Table
            if col_a == "구분" and col_b == "Element":
                parsing_layout = True
                continue
            
            if col_a == "Example":
                parsing_layout = False
                continue

            # 3. Parse Layout (Parameters)
            if parsing_layout:
                if col_a: 
                    current_category = col_a

                element = str(row[1]).strip() if pd.notna(row[1]) else ""
                
                if not element:
                    continue

                param_obj = {
                    "name": element,
                    "korean_name": str(row[2]).strip() if pd.notna(row[2]) else "",
                    "type": str(row[3]).strip() if pd.notna(row[3]) else "",
                    "required": True if str(row[4]).strip().upper() == "Y" else False,
                    "length": str(row[5]).strip() if pd.notna(row[5]) else "",
                    "description": str(row[6]).strip() if pd.notna(row[6]) else ""
                }

                if "Request Header" in current_category:
                    api_data["request"]["headers"].append(param_obj)
                elif "Request Query Parameter" in current_category:
                    api_data["request"]["query_parameters"].append(param_obj)
                elif "Request Body" in current_category:
                    api_data["request"]["body"].append(param_obj)
                elif "Response Header" in current_category:
                    api_data["response"]["headers"].append(param_obj)
                elif "Response Body" in current_category:
                    api_data["response"]["body"].append(param_obj)

            # 4. Extract Examples
            if "Request Example" in col_a:
                api_data["examples"]["request"] = col_b
            elif "Response Example" in col_a:
                api_data["examples"]["response"] = col_b

        # 5. Create Subfolder based on "메뉴 위치" (Category)
        raw_category = api_data["category"]
        if not raw_category:
            raw_category = "미분류" # Fallback if category is missing

        # Clean folder name (e.g., "[국내주식] 주문/계좌" -> "국내주식_주문_계좌")
        safe_folder_name = raw_category.replace("[", "").replace("] ", "_").replace("]", "").replace("/", "_").strip()
        
        category_dir = os.path.join(output_dir, safe_folder_name)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)

        # 6. Save the parsed data to a JSON file inside the subfolder
        safe_filename = str(sheet_name).replace("/", "_").replace("\\", "_").replace(" ", "_")
        output_file = os.path.join(category_dir, f"{safe_filename}.json")
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(api_data, f, ensure_ascii=False, indent=4)

    print(f"\n✅ Extraction complete! Files are grouped by category in the '{output_dir}' folder.")

if __name__ == "__main__":
    TARGET_EXCEL_FILE = "./KIS_open_API.xlsx" 
    process_kis_excel(TARGET_EXCEL_FILE)