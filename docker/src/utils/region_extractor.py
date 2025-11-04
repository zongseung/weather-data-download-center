"""
Region extraction utilities for weather data collection
"""

import csv
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def parse_ul(ul, path, results):
    """
    <ul> 아래의 <li>를 깊이 우선으로 순회하며
    3번째 자식의 outer <label>에서 텍스트(예: 서울특별시)를 추출.
    inner .blind <label>은 제거하고, 4번째 자식에 <ul>이 있으면 재귀 진입.
    """
    for li in ul.find_all("li", recursive=False):
        # 직접 자식 요소만
        children = [c for c in li.contents if isinstance(c, Tag)]
        if len(children) < 3:
            continue
        third = children[2]
        # blind 클래스 없는 outer label 선택
        outer_label = third.find("label", class_=lambda c: not c or "blind" not in c)
        if not outer_label:
            continue
        # inner blind label 제거
        blind = outer_label.find("label", class_="blind")
        if blind:
            blind.extract()
        name = outer_label.get_text(strip=True)
        new_path = path + [name]

        # 4번째 자식에 <ul>이 있으면 재귀
        if len(children) >= 4 and children[3].name == "ul":
            parse_ul(children[3], new_path, results)
        else:
            results.append(new_path)


def extract_regions(url: str = "https://data.kma.go.kr/data/rmt/rmtList.do?code=420&pgmNo=572", 
                   output_file: str = "regions.csv"):
    """
    기상청 웹사이트에서 행정구역 정보를 추출하여 CSV 파일로 저장
    
    Args:
        url: 기상청 행정구역 선택 페이지 URL
        output_file: 출력 CSV 파일명
    """
    # Selenium headless 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    root_ul = soup.select_one("#ztree_1_ul")
    if not root_ul:
        raise RuntimeError("#ztree_1_ul 을 찾을 수 없습니다.")

    all_paths = []
    parse_ul(root_ul, [], all_paths)

    # CSV 헤더 생성
    max_depth = max(len(p) for p in all_paths) if all_paths else 0
    headers = [f"Level{i+1}" for i in range(max_depth)]

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for path in all_paths:
            writer.writerow(path + [""] * (max_depth - len(path)))

    print(f"전체 {len(all_paths)}개 항목을 {output_file}에 저장했습니다.")
    return all_paths


def merge_region_data(input_file: str = "regions.csv", 
                     output_file: str = "지역코드.csv"):
    """
    행정구역 데이터를 병합하여 최종 지역코드 CSV 생성
    
    Args:
        input_file: 입력 CSV 파일명
        output_file: 출력 CSV 파일명
    """
    # 이 함수는 기존 행정구역데이터합치기.py의 기능을 구현
    # 현재는 기본적인 구현만 제공
    print(f"행정구역 데이터 병합: {input_file} -> {output_file}")
    # TODO: 실제 병합 로직 구현


def main():
    """메인 실행 함수"""
    try:
        regions = extract_regions()
        merge_region_data()
        print("행정구역 추출 완료")
    except Exception as e:
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()
