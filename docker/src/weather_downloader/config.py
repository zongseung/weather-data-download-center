"""
Configuration classes for weather data downloader
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class DownloadConfig:
    """Configuration for weather data download"""
    login_id: str
    password: str
    config_name: str
    start_date: datetime
    end_date: datetime
    variables: Optional[List[str]] = None  # JSON에서 받은 변수들


class WeatherConfig:
    """Weather data configuration constants"""
    
    CONFIGS = {
        "단기예보": {
            "code": "424",
            "api": "request420",
            "mode": "range",
            "reqst_purpose_cd": "F00415",
            "request_url": "https://data.kma.go.kr/mypage/rmt/callDtaReqstIrods4xxNewAjax.do",
            "selectType": "1",
        },
        "초단기실황": {
            "code": "400",
            "api": "request400",
            "mode": "monthly",
            "reqst_purpose_cd": "F00401",
            "request_url": "https://data.kma.go.kr/mypage/rmt/callDtaReqstIrods4xxAjax.do",
            "selectType": "1",
        },
        "초단기예보": {
            "code": "411",
            "api": "request410",
            "mode": "range",
            "reqst_purpose_cd": "F00415",
            "request_url": "https://data.kma.go.kr/mypage/rmt/callDtaReqstIrods4xxNewAjax.do",
            "selectType": "1",
        }
    }
    
    # 변수명 -> 코드 매핑
    VARIABLE_MAPPING = {
        "1시간기온": "TMP",
        "풍속": "WSD",
        "하늘상태": "SKY",
        "습도": "REH",
        "일최고기온": "TMX",
        "일최저기온": "TMN",
        "강수형태": "PTY",
        "강수확률": "POP",
        "동서바람성분": "UUU",
        "남북바람성분": "VVV",
        "1시간강수량": "PCP",
        "1시간적설": "SNO",
        "파고": "WAV",
        "풍향": "VEC"
    }
    
    # 기본 변수들 (하위 호환성)
    DEFAULT_VARIABLES = [
        {"name": "1시간기온", "code": "TMP"},
        {"name": "풍속", "code": "WSD"},
        {"name": "하늘상태", "code": "SKY"},
        {"name": "습도", "code": "REH"}
    ]
    
    @classmethod
    def get_config(cls, config_name: str) -> Dict:
        """Get configuration by name"""
        return cls.CONFIGS.get(config_name, {})
    
    @classmethod
    def get_variables(cls) -> List[Dict]:
        """Get default variables"""
        return cls.DEFAULT_VARIABLES
    
    @classmethod
    def get_variables_from_names(cls, variable_names: List[str]) -> List[Dict]:
        """Convert variable names to variable dicts with codes"""
        variables = []
        for name in variable_names:
            if name in cls.VARIABLE_MAPPING:
                variables.append({
                    "name": name,
                    "code": cls.VARIABLE_MAPPING[name]
                })
            else:
                print(f"Warning: Unknown variable name '{name}'")
        return variables