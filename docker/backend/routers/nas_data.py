from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import unicodedata
import os
from itertools import islice
from typing import Dict, Any

router = APIRouter(prefix="/api", tags=["nas"])


def resolve_nas_base_path() -> Path:
    """로컬 및 컨테이너 환경에서 NAS 기본 경로를 탐색합니다."""

    candidates = []

    env_path = os.getenv("WEATHER_DATA_PATH")
    if env_path:
        candidates.append(Path(env_path))

    candidates.extend(
        [
            Path("/nas-weather-data"),
            Path("/Volumes/nas-weather-data"),
            Path(__file__).resolve().parents[2] / "nas-weather-data",
        ]
    )

    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except OSError:
            # 접근 권한 문제 등이 발생한 경우 다음 후보를 시도
            continue

    # 어떤 후보도 존재하지 않는 경우, 가장 첫 번째 후보(환경변수 또는 기본 경로)를 반환
    return candidates[0]


NAS_BASE_PATH = resolve_nas_base_path()

def normalize_path(path_str: str) -> str:
    """macOS 한글 경로 정규화"""
    return unicodedata.normalize("NFC", path_str)


def build_file_path(
    forecast_type: str,
    city: str,
    district: str,
    town: str,
    variable: str,
    filename: str,
) -> Path:
    return (
        NAS_BASE_PATH
        / normalize_path(forecast_type)
        / normalize_path(city)
        / normalize_path(district)
        / normalize_path(town)
        / normalize_path(variable)
        / normalize_path(filename)
    )


def read_file_preview(file_path: Path, lines: int = 30) -> Dict[str, Any]:
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr"]
    for encoding in encodings:
        try:
            with file_path.open("r", encoding=encoding) as f:
                preview_lines = [line.rstrip("\n") for line in islice(f, lines)]
            return {"lines": preview_lines, "encoding": encoding}
        except UnicodeDecodeError:
            continue

    # 최종 fallback: 바이너리 모드에서 디코딩 오류 무시
    with file_path.open("rb") as f:
        preview_lines = []
        for _ in range(lines):
            chunk = f.readline()
            if not chunk:
                break
            preview_lines.append(chunk.decode("utf-8", errors="ignore").rstrip("\n"))

    return {"lines": preview_lines, "encoding": "unknown"}

@router.get("/nas/forecast-types")
def get_forecast_types():
    """
    NAS에 있는 예보 유형 목록을 반환합니다.
    """
    try:
        if not NAS_BASE_PATH.exists():
            raise HTTPException(status_code=404, detail=f"NAS 경로를 찾을 수 없습니다: {NAS_BASE_PATH}")
        
        forecast_types = []
        for item in NAS_BASE_PATH.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('#'):
                forecast_types.append({
                    "name": unicodedata.normalize("NFC", item.name),
                    "path": str(item)
                })
        
        return {
            "forecast_types": forecast_types,
            "total": len(forecast_types)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/cities")
def get_cities(forecast_type: str = Query(..., description="예보 유형 (단기예보, 초단기예보, 초단기실황)")):
    """
    특정 예보 유형의 시/도 목록을 반환합니다.
    """
    try:
        forecast_path = NAS_BASE_PATH / normalize_path(forecast_type)
        
        if not forecast_path.exists():
            raise HTTPException(status_code=404, detail=f"예보 유형을 찾을 수 없습니다: {forecast_type}")
        
        cities = []
        for item in forecast_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('#'):
                cities.append({
                    "name": unicodedata.normalize("NFC", item.name),
                    "path": str(item)
                })
        
        return {
            "forecast_type": forecast_type,
            "cities": sorted(cities, key=lambda x: x["name"]),
            "total": len(cities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/districts")
def get_districts(
    forecast_type: str = Query(..., description="예보 유형"),
    city: str = Query(..., description="시/도 이름")
):
    """
    특정 시/도의 구/군 목록을 반환합니다.
    """
    try:
        city_path = NAS_BASE_PATH / normalize_path(forecast_type) / normalize_path(city)
        
        if not city_path.exists():
            raise HTTPException(status_code=404, detail=f"경로를 찾을 수 없습니다: {city_path}")
        
        districts = []
        for item in city_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('#'):
                districts.append({
                    "name": unicodedata.normalize("NFC", item.name),
                    "path": str(item)
                })
        
        return {
            "forecast_type": forecast_type,
            "city": city,
            "districts": sorted(districts, key=lambda x: x["name"]),
            "total": len(districts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/towns")
def get_towns(
    forecast_type: str = Query(..., description="예보 유형"),
    city: str = Query(..., description="시/도 이름"),
    district: str = Query(..., description="구/군 이름")
):
    """
    특정 구/군의 동/읍/면 목록을 반환합니다.
    """
    try:
        district_path = NAS_BASE_PATH / normalize_path(forecast_type) / normalize_path(city) / normalize_path(district)
        
        if not district_path.exists():
            raise HTTPException(status_code=404, detail=f"경로를 찾을 수 없습니다: {district_path}")
        
        towns = []
        for item in district_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('#'):
                towns.append({
                    "name": unicodedata.normalize("NFC", item.name),
                    "path": str(item)
                })
        
        return {
            "forecast_type": forecast_type,
            "city": city,
            "district": district,
            "towns": sorted(towns, key=lambda x: x["name"]),
            "total": len(towns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/files")
def get_files(
    forecast_type: str = Query(..., description="예보 유형"),
    city: str = Query(..., description="시/도 이름"),
    district: str = Query(..., description="구/군 이름"),
    town: str = Query(..., description="동/읍/면 이름")
):
    """
    특정 동/읍/면의 실제 CSV 파일 목록을 반환합니다.
    """
    try:
        town_path = NAS_BASE_PATH / normalize_path(forecast_type) / normalize_path(city) / normalize_path(district) / normalize_path(town)
        
        if not town_path.exists():
            raise HTTPException(status_code=404, detail=f"경로를 찾을 수 없습니다: {town_path}")
        
        files_info = []
        variables = {}
        
        # 변수별로 그룹화
        for item in town_path.rglob("*.csv"):
            if item.is_file():
                # 파일 정보 추출
                relative_path = item.relative_to(town_path)
                parts = list(relative_path.parts)
                
                # 변수명 추출 (디렉토리 구조인 경우)
                if len(parts) > 1:
                    variable = unicodedata.normalize("NFC", parts[0])
                else:
                    # 파일명에서 변수명 추출
                    filename = item.name
                    parts_name = filename.replace('.csv', '').split('_')
                    if len(parts_name) >= 2:
                        variable = unicodedata.normalize("NFC", parts_name[1])
                    else:
                        variable = "기타"
                
                if variable not in variables:
                    variables[variable] = []
                
                # 파일명에서 날짜 정보 추출
                filename = item.name
                file_parts = filename.replace('.csv', '').split('_')
                start_date = file_parts[-2] if len(file_parts) >= 2 else ""
                end_date = file_parts[-1] if len(file_parts) >= 1 else ""
                
                variables[variable].append({
                    "filename": filename,
                    "path": str(item),
                    "size": item.stat().st_size,
                    "size_mb": round(item.stat().st_size / (1024 * 1024), 2),
                    "start_date": start_date,
                    "end_date": end_date,
                    "modified": item.stat().st_mtime
                })
        
        # 변수별로 정렬
        for var in variables:
            variables[var].sort(key=lambda x: x["start_date"])
        
        return {
            "forecast_type": forecast_type,
            "city": city,
            "district": district,
            "town": town,
            "variables": variables,
            "total_files": sum(len(files) for files in variables.values()),
            "total_variables": len(variables)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/data-summary")
def get_data_summary():
    """
    NAS에 있는 전체 데이터 요약 정보를 반환합니다.
    """
    try:
        if not NAS_BASE_PATH.exists():
            raise HTTPException(status_code=404, detail=f"NAS 경로를 찾을 수 없습니다: {NAS_BASE_PATH}")
        
        summary = {
            "nas_path": str(NAS_BASE_PATH),
            "nas_available": True,
            "forecast_types": []
        }
        
        for forecast_dir in NAS_BASE_PATH.iterdir():
            if forecast_dir.is_dir() and not forecast_dir.name.startswith('.') and not forecast_dir.name.startswith('#'):
                forecast_info = {
                    "name": unicodedata.normalize("NFC", forecast_dir.name),
                    "cities": []
                }
                
                city_count = 0
                district_count = 0
                town_count = 0
                
                for city_dir in forecast_dir.iterdir():
                    if city_dir.is_dir() and not city_dir.name.startswith('.') and not city_dir.name.startswith('#'):
                        city_count += 1
                        for district_dir in city_dir.iterdir():
                            if district_dir.is_dir() and not district_dir.name.startswith('.') and not district_dir.name.startswith('#'):
                                district_count += 1
                                for town_dir in district_dir.iterdir():
                                    if town_dir.is_dir() and not town_dir.name.startswith('.') and not town_dir.name.startswith('#'):
                                        town_count += 1
                
                forecast_info["city_count"] = city_count
                forecast_info["district_count"] = district_count
                forecast_info["town_count"] = town_count
                summary["forecast_types"].append(forecast_info)
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/download")
def download_file(
    forecast_type: str = Query(..., description="예보 유형"),
    city: str = Query(..., description="시/도 이름"),
    district: str = Query(..., description="구/군 이름"),
    town: str = Query(..., description="동/읍/면 이름"),
    variable: str = Query(..., description="예보 변수"),
    filename: str = Query(..., description="파일명")
):
    """
    특정 CSV 파일을 다운로드합니다.
    """
    try:
        file_path = build_file_path(forecast_type, city, district, town, variable, filename)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"유효한 파일이 아닙니다: {filename}")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="text/csv"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/file-preview")
def get_file_preview(
    forecast_type: str = Query(..., description="예보 유형"),
    city: str = Query(..., description="시/도 이름"),
    district: str = Query(..., description="구/군 이름"),
    town: str = Query(..., description="동/읍/면 이름"),
    variable: str = Query(..., description="예보 변수"),
    filename: str = Query(..., description="파일명"),
    lines: int = Query(30, ge=1, le=200, description="미리보기 라인 수 (최대 200)"),
):
    """CSV 파일의 앞부분을 미리보기로 반환합니다."""

    try:
        file_path = build_file_path(forecast_type, city, district, town, variable, filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"유효한 파일이 아닙니다: {filename}")

        preview = read_file_preview(file_path, lines=lines)

        return {
            "forecast_type": forecast_type,
            "city": city,
            "district": district,
            "town": town,
            "variable": variable,
            "filename": filename,
            "encoding": preview["encoding"],
            "lines": preview["lines"],
            "line_count": len(preview["lines"]),
            "requested_lines": lines,
            "size": file_path.stat().st_size,
            "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")


@router.get("/nas/variables")
def get_variables(
    forecast_type: str = Query(..., description="예보 유형"),
    city: str = Query(..., description="시/도 이름"),
    district: str = Query(..., description="구/군 이름"),
    town: str = Query(..., description="동/읍/면 이름")
):
    """
    특정 동/읍/면의 예보 변수(폴더) 목록을 반환합니다.
    """
    try:
        town_path = (
            NAS_BASE_PATH 
            / normalize_path(forecast_type) 
            / normalize_path(city) 
            / normalize_path(district) 
            / normalize_path(town)
        )
        
        if not town_path.exists():
            raise HTTPException(status_code=404, detail=f"경로를 찾을 수 없습니다: {town_path}")
        
        variables = []
        for item in town_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and not item.name.startswith('#'):
                # 해당 변수 폴더의 파일 개수 확인
                file_count = len(list(item.glob("*.csv")))
                if file_count > 0:
                    # 첫 번째 파일의 정보 가져오기
                    first_file = next(item.glob("*.csv"), None)
                    if first_file:
                        variables.append({
                            "name": unicodedata.normalize("NFC", item.name),
                            "file_count": file_count,
                            "path": str(item)
                        })
        
        return {
            "forecast_type": forecast_type,
            "city": city,
            "district": district,
            "town": town,
            "variables": sorted(variables, key=lambda x: x["name"]),
            "total": len(variables)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

@router.get("/nas/variable-files")
def get_variable_files(
    forecast_type: str = Query(..., description="예보 유형"),
    city: str = Query(..., description="시/도 이름"),
    district: str = Query(..., description="구/군 이름"),
    town: str = Query(..., description="동/읍/면 이름"),
    variable: str = Query(..., description="예보 변수")
):
    """
    특정 예보 변수의 파일 목록을 반환합니다.
    """
    try:
        variable_path = (
            NAS_BASE_PATH 
            / normalize_path(forecast_type) 
            / normalize_path(city) 
            / normalize_path(district) 
            / normalize_path(town) 
            / normalize_path(variable)
        )
        
        if not variable_path.exists():
            raise HTTPException(status_code=404, detail=f"경로를 찾을 수 없습니다: {variable_path}")
        
        files = []
        for item in variable_path.glob("*.csv"):
            if item.is_file():
                # 파일명에서 날짜 정보 추출
                filename = item.name
                file_parts = filename.replace('.csv', '').split('_')
                start_date = file_parts[-2] if len(file_parts) >= 2 else ""
                end_date = file_parts[-1] if len(file_parts) >= 1 else ""
                
                files.append({
                    "filename": filename,
                    "size": item.stat().st_size,
                    "size_mb": round(item.stat().st_size / (1024 * 1024), 2),
                    "start_date": start_date,
                    "end_date": end_date,
                    "modified": item.stat().st_mtime
                })
        
        return {
            "forecast_type": forecast_type,
            "city": city,
            "district": district,
            "town": town,
            "variable": variable,
            "files": sorted(files, key=lambda x: x["start_date"]),
            "total": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {e}")

