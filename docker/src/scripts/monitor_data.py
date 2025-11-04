#!/usr/bin/env python3
"""
기상 데이터 수집 상태 모니터링 스크립트
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
import pandas as pd


class DataMonitor:
    def __init__(self, nas_path="/mnt/nvme/weather-data/data/nas-weather-data"):
        self.nas_path = Path(nas_path)
        self.stats_file = self.nas_path / "collection_stats.json"
        
    def scan_directory(self):
        """디렉토리 스캔하여 데이터 수집 현황 파악"""
        stats = {
            "scan_time": datetime.now().isoformat(),
            "total_files": 0,
            "total_size_mb": 0,
            "regions": {},
            "configs": {},
            "variables": {},
            "date_range": {"earliest": None, "latest": None}
        }
        
        if not self.nas_path.exists():
            return stats
            
        # nas-weather-data 디렉토리 직접 스캔
        if self.nas_path.exists():
            for root, dirs, files in os.walk(self.nas_path):
                for file in files:
                    if file.endswith('.csv'):
                        file_path = Path(root) / file
                        file_size = file_path.stat().st_size
                        
                        stats["total_files"] += 1
                        stats["total_size_mb"] += file_size / (1024 * 1024)
                        
                        # 파일 경로에서 정보 추출
                        self._analyze_file_path(file_path, stats)
        
        return stats
    
    def _analyze_file_path(self, file_path, stats):
        """파일 경로 분석하여 통계 업데이트"""
        try:
            # 경로: data/nas-weather-data/단기예보/서울특별시/강남구/역삼동/기온/파일명.csv
            parts = file_path.parts
            
            if len(parts) >= 6:
                config_name = parts[-5]  # 단기예보
                level1 = parts[-4]       # 서울특별시
                level2 = parts[-3]       # 강남구
                level3 = parts[-2]       # 역삼동
                variable = parts[-1].split('_')[0]  # 기온
                
                # 지역별 통계
                region_key = f"{level1}/{level2}/{level3}"
                if region_key not in stats["regions"]:
                    stats["regions"][region_key] = 0
                stats["regions"][region_key] += 1
                
                # 설정별 통계
                if config_name not in stats["configs"]:
                    stats["configs"][config_name] = 0
                stats["configs"][config_name] += 1
                
                # 변수별 통계
                if variable not in stats["variables"]:
                    stats["variables"][variable] = 0
                stats["variables"][variable] += 1
                
                # 날짜 범위 분석
                filename = parts[-1]
                if '_' in filename:
                    date_parts = filename.split('_')
                    if len(date_parts) >= 3:
                        try:
                            date_str = date_parts[-2]  # YYYYMMDD 형식
                            if len(date_str) == 8:
                                file_date = datetime.strptime(date_str, '%Y%m%d')
                                
                                if stats["date_range"]["earliest"] is None or file_date < datetime.fromisoformat(stats["date_range"]["earliest"]):
                                    stats["date_range"]["earliest"] = file_date.isoformat()
                                    
                                if stats["date_range"]["latest"] is None or file_date > datetime.fromisoformat(stats["date_range"]["latest"]):
                                    stats["date_range"]["latest"] = file_date.isoformat()
                        except ValueError:
                            pass
                            
        except Exception as e:
            print(f"파일 경로 분석 오류: {e}")
    
    def save_stats(self, stats):
        """통계를 JSON 파일로 저장"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    def load_stats(self):
        """저장된 통계 로드"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def print_stats(self, stats):
        """통계 출력"""
        print(f"\n=== 기상 데이터 수집 현황 ({stats['scan_time']}) ===")
        print(f"총 파일 수: {stats['total_files']:,}개")
        print(f"총 용량: {stats['total_size_mb']:.2f} MB")
        
        if stats['date_range']['earliest'] and stats['date_range']['latest']:
            print(f"데이터 기간: {stats['date_range']['earliest']} ~ {stats['date_range']['latest']}")
        
        print(f"\n지역별 파일 수:")
        for region, count in sorted(stats['regions'].items()):
            print(f"  {region}: {count}개")
        
        print(f"\n설정별 파일 수:")
        for config, count in sorted(stats['configs'].items()):
            print(f"  {config}: {count}개")
        
        print(f"\n변수별 파일 수:")
        for variable, count in sorted(stats['variables'].items()):
            print(f"  {variable}: {count}개")
    
    def monitor_loop(self, interval=60):
        """지속적인 모니터링"""
        print(f"데이터 수집 모니터링 시작 (간격: {interval}초)")
        print("Ctrl+C로 종료")
        
        try:
            while True:
                stats = self.scan_directory()
                self.save_stats(stats)
                self.print_stats(stats)
                print("-" * 50)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n모니터링 종료")


def main():
    monitor = DataMonitor()
    
    # 한 번만 스캔
    stats = monitor.scan_directory()
    monitor.save_stats(stats)
    monitor.print_stats(stats)
    
    # 지속적 모니터링을 원하면 아래 주석 해제
    monitor.monitor_loop(interval=30)


if __name__ == "__main__":
    main()
