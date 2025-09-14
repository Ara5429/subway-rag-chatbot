# naver_search.py
import os
import re
import datetime
from typing import Optional, Tuple, List

import requests
from dotenv import load_dotenv

load_dotenv()
NAVER_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_SECRET = os.getenv("NAVER_CLIENT_SECRET")


# ─────────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────────
def _headers() -> dict:
    if not (NAVER_ID and NAVER_SECRET):
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다.")
    return {
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET,
    }

def _strip_tags(s: str) -> str:
    return (s or "").replace("<b>", "").replace("</b>", "")


# ─────────────────────────────────────────────
# 역/출구 파서
# ─────────────────────────────────────────────
def parse_station_exit(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    예)
      - '가락시장역 2번 출구'
      - '가락시장역2번출구'
      - '가락시장역 2-1번출구'
      - '가락시장역'
    반환: (station, exit_no)
      - ("가락시장역", "2"), ("가락시장역", "2-1"), ("가락시장역", None)
      - 없으면 (None, None)
    """
    if not text:
        return None, None

    # 1) 공백 제거 형태: '가락시장역2번출구', '가락시장역2-1번출구'
    normalized = re.sub(r"\s+", "", text)
    m = re.search(r"([가-힣A-Za-z0-9]+역)(\d+(?:-\d+)?)번출구", normalized)
    if m:
        return m.group(1), m.group(2)

    # 2) 일반 공백 포함: '가락시장역 2번 출구', '가락시장역 2-1번 출구'
    m = re.search(r"([가-힣A-Za-z0-9]+역)\s*(\d+(?:-\d+)?)\s*번\s*출구", text)
    if m:
        return m.group(1), m.group(2)

    # 3) 역명만 있는 경우
    m = re.search(r"([가-힣A-Za-z0-9]+역)", text)
    if m:
        return m.group(1), None

    return None, None


# ─────────────────────────────────────────────
# 네이버 로컬(장소) 검색
# ─────────────────────────────────────────────
def naver_local_search(query: str, display: int = 10, sort: str = "comment") -> List[dict]:
    """
    네이버 로컬(장소) 검색.
    sort: 'random' | 'comment' (리뷰 많은 순)
    """
    url = "https://openapi.naver.com/v1/search/local.json"
    params = {"query": query, "display": min(display, 30), "start": 1, "sort": sort}
    res = requests.get(url, headers=_headers(), params=params, timeout=10)
    res.raise_for_status()
    return res.json().get("items", [])


def build_naver_places_context(
    station: Optional[str],
    exit_no: Optional[str],
    keyword: str = "맛집",
    top_k: int = 5
) -> str:
    """
    '가락시장역 2번 출구 맛집' → 후보 상위 top_k를 텍스트 요약으로 변환
    """
    base = (
        f"{station} {exit_no}번 출구 {keyword}"
        if (station and exit_no) else
        (f"{station} {keyword}" if station else keyword)
    )

    items = naver_local_search(base, display=top_k * 2, sort="comment")
    # 간단 랭킹: 역명/지명 포함 가산점
    if station and items:
        key = station.replace("역", "")
        def score(it):
            t = _strip_tags(it.get("title", ""))
            ra = it.get("roadAddress", "") or it.get("address", "")
            s = 0
            if key and key in t:  s += 2
            if key and key in ra: s += 2
            # 가락시장 특수 키워드(예: '가락') 가산 (원하면 확장)
            if "가락" in (t + ra): s += 1
            return s
        items = sorted(items, key=score, reverse=True)

    if not items:
        return f"[네이버 로컬] '{base}' 결과 없음"

    lines = [f"[네이버 로컬] '{base}' 후보 상위 {min(top_k, len(items))}개"]
    for i, it in enumerate(items[:top_k], 1):
        title = _strip_tags(it.get("title", ""))
        cat   = it.get("category", "")
        road  = it.get("roadAddress", "") or it.get("address", "")
        tel   = it.get("telephone", "")
        link  = it.get("link", "")
        lines.append(
            f"{i}. {title} · {cat}\n"
            f"   주소: {road}\n"
            f"   전화: {tel}\n"
            f"   링크: {link}"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────
# 네이버 블로그 검색
# ─────────────────────────────────────────────
def naver_blog_search(query: str, days: int = 30, display: int = 30) -> List[dict]:
    """
    네이버 블로그 검색 (최신순) 후 최근 N일 이내만 필터
    """
    url = "https://openapi.naver.com/v1/search/blog.json"
    params = {"query": query, "display": min(display, 100), "sort": "date"}
    res = requests.get(url, headers=_headers(), params=params, timeout=10)
    res.raise_for_status()
    items = res.json().get("items", [])
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y%m%d")
    return [it for it in items if it.get("postdate", "00000000") >= cutoff]


def build_naver_blog_context(
    query: str,
    station: Optional[str] = None,
    days: int = 30,
    max_items: int = 8
) -> str:
    """
    네이버 블로그 결과를 모델 컨텍스트용 텍스트로 변환.
    station이 주어지면 제목/요약에 해당 역명이 포함된 글을 우선 사용.
    """
    items = naver_blog_search(query, days=days, display=max_items * 3)

    if station and items:
        key = station.replace("역", "")
        filtered = []
        for it in items:
            text = _strip_tags(
                (it.get("title", "") or "") + " " + (it.get("description", "") or "")
            )
            if (station in text) or (key and key in text):
                filtered.append(it)
        if filtered:
            items = filtered

    if not items:
        return f"[네이버 블로그] 최근 {days}일 '{query}' 결과 없음"

    head = f"[네이버 블로그] 최근 {days}일 '{query}' 관련 글"
    if station:
        head += f" (역 필터: {station})"
    lines = [head]

    for b in items[:max_items]:
        title = _strip_tags(b.get("title", ""))
        desc  = _strip_tags(b.get("description", ""))
        date  = b.get("postdate", "")
        link  = b.get("link", "")
        lines.append(f"- {title} ({date})\n  요약: {desc}\n  링크: {link}")

    return "\n".join(lines)
