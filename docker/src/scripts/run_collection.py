#!/usr/bin/env python3
"""
기상 데이터 수집 실행 스크립트
설정 파일을 읽어서 weather_downloader.py를 실행
"""

import json
import asyncio
import logging
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weather_downloader import WeatherDownloader, DownloadConfig

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_file="config.json"):
    """설정 파일 로드"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_file}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"설정 파일 JSON 파싱 오류: {e}")
        return None


def progress_callback(current: int, total: int, message: str):
    """진행률 콜백"""
    percentage = (current / total) * 100
    logger.info(f"[{current}/{total}] {percentage:.1f}% - {message}")


def file_callback(file_path: str):
    """파일 저장 콜백"""
    logger.info(f"파일 저장됨: {file_path}")


async def run_collection(config_data):
    """데이터 수집 실행"""
    
    login_id = config_data["login"]["id"]
    password = config_data["login"]["password"]
    
    if login_id == "YOUR_LOGIN_ID" or password == "YOUR_PASSWORD":
        logger.error("설정 파일에서 로그인 정보를 설정해주세요!")
        logger.error("config.json 파일을 열어서 YOUR_LOGIN_ID와 YOUR_PASSWORD를 실제 값으로 변경하세요.")
        return
    
    downloader = WeatherDownloader()
    
    # 설정에서 예보 타입과 변수 읽기
    forecast_types = config_data.get("forecast_types", ["단기예보", "초단기실황", "초단기예보"])
    variables_by_type = config_data.get("variables_by_type", {})
    start_date = datetime.strptime(config_data["date_range"]["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(config_data["date_range"]["end_date"], "%Y-%m-%d")
    
    logger.info(f"=== 전체 기상 데이터 수집 시작 ===")
    logger.info(f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"수집 타입: {', '.join(forecast_types)}")
    
    for config_name in forecast_types:
        # 예보 타입별 변수 가져오기
        variables = variables_by_type.get(config_name, ["1시간기온", "풍속", "하늘상태", "습도"])
        logger.info(f"\n=== {config_name} 데이터 수집 시작 ===")
        logger.info(f"수집 변수: {', '.join(variables)}")
        
        config = DownloadConfig(
            login_id=login_id,
            password=password,
            config_name=config_name,
            start_date=start_date,
            end_date=end_date,
            variables=variables  # 변수 정보 전달
        )
        
        try:
            await downloader.download(config, progress_callback, file_callback)
            logger.info(f"=== {config_name} 데이터 수집 완료 ===")
        except Exception as e:
            logger.error(f"=== {config_name} 데이터 수집 실패: {e} ===")
            continue


def main():
    """메인 실행 함수"""
    logger.info("기상 데이터 수집 시작")
    
    # 설정 로드
    config_data = load_config()
    if not config_data:
        return
    
    # 데이터 수집 실행
    asyncio.run(run_collection(config_data))
    
    logger.info("모든 데이터 수집 완료")


if __name__ == "__main__":
    main()
