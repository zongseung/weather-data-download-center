"""
Main weather data downloader class
"""

import os
import zipfile
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import asyncio
import time
from typing import List, Dict, Callable, Optional
import logging
import csv

from .config import DownloadConfig, WeatherConfig

logger = logging.getLogger(__name__)


class WeatherDownloader:
    """Weather data downloader class"""
    
    def __init__(self):
        self.session = requests.Session()
        self.configs = WeatherConfig.CONFIGS
    
    def load_regions_from_csv(self, csv_file: str = "지역코드.csv") -> List[Dict]:
        """CSV 파일에서 지역 정보를 읽어옵니다."""
        regions = []
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    regions.append({
                        "level1": row["Level1"],
                        "level2": row["Level2"], 
                        "level3": row["Level3"],
                        "code": row["ReqList_Last"]
                    })
            logger.info(f"CSV에서 {len(regions)}개 지역을 로드했습니다.")
            return regions
        except FileNotFoundError:
            logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_file}")
            return []
        except Exception as e:
            logger.error(f"CSV 파일 읽기 오류: {e}")
            return []
    
    def get_variables_from_existing_code(self) -> List[Dict]:
        """기존 코드에서 변수 정보를 가져옵니다."""
        return WeatherConfig.get_variables()
    
    def get_cookie(self, login_id: str, password: str) -> str:
        """기상청 로그인 및 쿠키 획득"""
        logger.info("기상청 로그인 중...")
        url = "https://data.kma.go.kr/login/loginAjax.do"
        resp = self.session.post(url, data={"loginId": login_id, "passwordNo": password})
        resp.raise_for_status()
        cookies = self.session.cookies.get_dict()
        time.sleep(2)  # 로그인 후 잠시 대기
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])
    
    def make_headers(self, cookie: str):
        """요청 헤더 생성"""
        first = {
            "Accept": "text/plain, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": cookie,
            "Host": "data.kma.go.kr",
            "Origin": "https://data.kma.go.kr",
            "Referer": "https://data.kma.go.kr/data/rmt/rmtList.do",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        
        second = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": cookie,
            "Host": "data.kma.go.kr",
            "Origin": "https://data.kma.go.kr",
            "Referer": "https://data.kma.go.kr/data/rmt/rmtList.do",
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        
        return first, second
    
    def generate_intervals(self, start: datetime, end: datetime, mode: str):
        """날짜 구간 생성"""
        intervals = []
        if mode == "monthly":
            current = start.replace(day=1)
            while current <= end:
                intervals.append((current.strftime("%Y%m"), current.strftime("%Y%m")))
                current += relativedelta(months=1)
        else:  # range mode
            current = start
            while current < end:
                next_date = current + relativedelta(months=1)
                if next_date > end:
                    next_date = end
                intervals.append((current.strftime("%Y%m%d"), next_date.strftime("%Y%m%d")))
                current = next_date
        return intervals
    
    def generate_request_body(self, var_name: str, var_code: str, start: str, end: str, 
                            station: str, region_code: str, config: Dict):
        """요청 본문 생성"""
        return {
            "apiCd": config["api"],
            "data_code": config["code"],
            "hour": "",
            "pageIndex": "1",
            "from": start,
            "to": end,
            "reqst_purpose_cd": config["reqst_purpose_cd"],
            "recordCountPerPage": "10",
            "txtVar1Nm": var_name,
            "selectType": config["selectType"],
            "startDt": start[:4],
            "startMt": start[4:6],
            "endDt": end[:4],
            "endMt": end[4:6],
            "from_": start,
            "to_": end,
            "var1": var_code,
            "var3": region_code,
            "stnm": station,
            "elcd": var_name,
            "strtm": start,
            "endtm": end,
            "req_list": f"{start}|{end}|{config['code']}|{var_code}|{region_code}",
        }
    
    async def download(self, config: DownloadConfig, 
                      progress_callback: Callable[[int, int, str], None],
                      file_callback: Callable[[str], None],
                      csv_file: str = "지역코드.csv"):
        """메인 다운로드 함수"""
        try:
            # 로그인
            cookie = self.get_cookie(config.login_id, config.password)
            hdr1, hdr2 = self.make_headers(cookie)
            
            # CSV에서 지역 정보 로드
            regions = self.load_regions_from_csv(csv_file)
            if not regions:
                logger.error("지역 정보를 로드할 수 없습니다.")
                return
            
            # JSON 설정에서 변수 정보 가져오기 (우선순위)
            if config.variables:
                variables = WeatherConfig.get_variables_from_names(config.variables)
            else:
                # 기본 변수 사용
                variables = self.get_variables_from_existing_code()
            
            # 설정 가져오기
            cfg = self.configs[config.config_name]
            
            # 날짜 구간 생성
            intervals = self.generate_intervals(config.start_date, config.end_date, cfg["mode"])
            
            # 전체 작업 수 계산
            total_tasks = len(regions) * len(intervals) * len(variables)
            current_task = 0
            
            # 다운로드 디렉토리 생성
            base_dir = os.path.join("data", "nas-weather-data", config.config_name)
            os.makedirs(base_dir, exist_ok=True)
            
            for region in regions:
                region_dir = os.path.join(base_dir, region["level1"], region["level2"], region["level3"])
                os.makedirs(region_dir, exist_ok=True)
                
                for start, end in intervals:
                    for variable in variables:
                        current_task += 1
                        var_name = variable["name"]
                        var_code = variable["code"]
                        
                        progress_callback(
                            current_task, 
                            total_tasks, 
                            f"{region['level3']} - {var_name} ({start}~{end})"
                        )
                        
                        # 파일이 이미 존재하는지 확인
                        expected_csv = f"{region['level3']}_{var_name}_{start}_{end}.csv"
                        var_dir = os.path.join(region_dir, var_name)
                        csv_path = os.path.join(var_dir, expected_csv)
                        
                        if os.path.exists(csv_path):
                            logger.info(f"파일이 이미 존재함: {csv_path}")
                            continue
                        
                        try:
                            # 데이터 요청
                            req_body = self.generate_request_body(
                                var_name, var_code, start, end,
                                region["level3"], region["code"], cfg
                            )
                            
                            # 데이터 생성 요청
                            self.session.post(cfg["request_url"], headers=hdr1, data=req_body)
                            
                            # 파일 다운로드 요청
                            download_payload = {"downFile": f"{region['level3']}_{var_name}_{start}_{end}.csv"}
                            response = self.session.post(
                                "https://data.kma.go.kr/data/rmt/downloadZip.do",
                                headers=hdr2,
                                data=download_payload,
                                stream=True
                            )
                            
                            if response.status_code == 200:
                                # ZIP 파일 저장
                                zip_path = os.path.join(region_dir, f"{region['level3']}_{var_name}_{start}_{end}.zip")
                                with open(zip_path, "wb") as f:
                                    for chunk in response.iter_content(8192):
                                        f.write(chunk)
                                
                                # ZIP 파일 압축 해제
                                os.makedirs(var_dir, exist_ok=True)
                                with zipfile.ZipFile(zip_path) as z:
                                    for info in z.infolist():
                                        try:
                                            filename = info.filename.encode("cp437").decode("euc-kr")
                                        except:
                                            filename = info.filename
                                        
                                        target_path = os.path.join(var_dir, filename)
                                        with open(target_path, "wb") as out_f:
                                            out_f.write(z.read(info.filename))
                                        
                                        file_callback(target_path)
                                
                                # ZIP 파일 삭제
                                os.remove(zip_path)
                                logger.info(f"다운로드 완료: {csv_path}")
                            else:
                                logger.error(f"다운로드 실패: {response.status_code}")
                                
                        except Exception as e:
                            logger.error(f"개별 다운로드 실패: {e}")
                            # 로그인 재시도
                            cookie = self.get_cookie(config.login_id, config.password)
                            hdr1, hdr2 = self.make_headers(cookie)
                        
                        # 요청 간 딜레이
                        await asyncio.sleep(0.5)
            
            logger.info("모든 다운로드 완료")
            
        except Exception as e:
            logger.error(f"다운로드 중 오류 발생: {e}")
            raise
