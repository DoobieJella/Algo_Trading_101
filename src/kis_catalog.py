from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


API_INDEX_SHEET = "API 목록"


@dataclass(frozen=True)
class KisEndpoint:
    sequence: str
    communication: str
    category: str
    api_name: str
    api_id: str
    tr_id_real: str
    tr_id_mock: str
    method: str
    path: str
    real_domain: str
    mock_domain: str

    @property
    def supports_virtual(self):
        return bool(self.mock_domain) and "미지원" not in self.mock_domain and "미지원" not in self.tr_id_mock

    @property
    def is_get(self):
        return self.method.upper() == "GET"

    @property
    def is_domestic_stock_quote(self):
        return self.category == "[국내주식] 기본시세"


def load_kis_endpoint_catalog(workbook_path=Path("KIS/KIS_open_API.xlsx")):
    workbook_path = Path(workbook_path)
    rows = _read_sheet_rows(workbook_path, API_INDEX_SHEET)
    if not rows:
        return []

    header = rows[0]
    endpoints = []
    for row in rows[1:]:
        values = _row_to_record(header, row)
        if not values.get("API 명"):
            continue
        endpoints.append(
            KisEndpoint(
                sequence=values.get("순번", ""),
                communication=values.get("API 통신방식", ""),
                category=values.get("메뉴 위치", ""),
                api_name=values.get("API 명", ""),
                api_id=values.get("API ID", ""),
                tr_id_real=values.get("실전 TR_ID", ""),
                tr_id_mock=values.get("모의 TR_ID", ""),
                method=values.get("HTTP Method", ""),
                path=values.get("URL 명", ""),
                real_domain=values.get("실전 Domain", ""),
                mock_domain=values.get("모의 Domain", ""),
            )
        )
    return endpoints


def domestic_stock_data_endpoints(endpoints):
    return [
        endpoint
        for endpoint in endpoints
        if endpoint.communication.upper() == "REST"
        and endpoint.is_get
        and endpoint.is_domestic_stock_quote
        and endpoint.supports_virtual
    ]


def find_endpoint(endpoints, api_name):
    for endpoint in endpoints:
        if endpoint.api_name == api_name:
            return endpoint
    raise ValueError(f"KIS endpoint not found: {api_name}")


def _row_to_record(header, row):
    return {
        column: row[index] if index < len(row) else ""
        for index, column in enumerate(header)
    }


def _read_sheet_rows(workbook_path, sheet_name):
    ns = {
        "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    with ZipFile(workbook_path) as workbook:
        shared_strings = _read_shared_strings(workbook, ns)
        sheet_path = _find_sheet_path(workbook, sheet_name, ns)
        sheet = ET.fromstring(workbook.read(sheet_path))
        rows = []
        for row in sheet.findall(".//m:sheetData/m:row", ns):
            values = []
            for cell in row.findall("m:c", ns):
                values.append(_read_cell_value(cell, shared_strings, ns))
            rows.append(values)
        return rows


def _read_shared_strings(workbook, ns):
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []

    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    values = []
    for item in root.findall("m:si", ns):
        values.append("".join(text.text or "" for text in item.findall(".//m:t", ns)))
    return values


def _find_sheet_path(workbook, sheet_name, ns):
    workbook_xml = ET.fromstring(workbook.read("xl/workbook.xml"))
    rels_xml = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    relationships = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_xml
    }
    for sheet in workbook_xml.find("m:sheets", ns):
        if sheet.attrib["name"] == sheet_name:
            rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = relationships[rel_id].lstrip("/")
            return f"xl/{target}"
    raise ValueError(f"Workbook sheet not found: {sheet_name}")


def _read_cell_value(cell, shared_strings, ns):
    value = cell.find("m:v", ns)
    if value is None:
        inline = cell.find("m:is/m:t", ns)
        return inline.text if inline is not None and inline.text is not None else ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(value.text)]
    return value.text or ""
