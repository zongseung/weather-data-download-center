"""
Cookie management utilities
"""

import requests


def get_cookie(login_id: str = "", password: str = "yuseong0745%"):
    """
    기상청 로그인 및 쿠키 획득
    
    Args:
        login_id: 기상청 계정 ID
        password: 기상청 계정 비밀번호
    
    Returns:
        str: 쿠키 문자열
    """
    login_url = "https://data.kma.go.kr/login/loginAjax.do"
    session = requests.Session()
    response = session.post(
        login_url,
        data={
            "loginId": login_id,
            "passwordNo": password,
        },
    )
    if response.status_code == 200:
        cookies = session.cookies.get_dict()
        cookie_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])
        return cookie_str
    else:
        raise Exception("Failed to retrieve cookies from KMA login page.")


if __name__ == "__main__":
    try:
        cookie = get_cookie()
        print("Successfully retrieved cookie:")
        print(cookie)
    except Exception as e:
        print(f"Error: {e}")
