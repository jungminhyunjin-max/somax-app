"""Seed content catalog for the recommendation engine.

Each item is tagged with the risk states (from CueSoma's biosignal + cycle
model) it is meant to address. "stable" items are shown when no elevated
risk is detected.
"""

RISK_STATES = ["pms", "stress", "binge", "stable"]

CATEGORIES = ["exercise", "diet", "cbt"]

CONTENT_ITEMS = [
    # PMS
    {"id": "ex_pms_gentle_yoga", "category": "exercise", "title": "골반 이완 요가 시퀀스",
     "description": "황체기 인대 이완을 고려한 저강도 골반·허리 이완 요가.", "target_contexts": ["pms"]},
    {"id": "ex_pms_walk", "category": "exercise", "title": "가벼운 걷기 루틴 15분",
     "description": "PMS 구간 컨디션 저하 시 부담 적은 유산소 루틴.", "target_contexts": ["pms"]},
    {"id": "diet_pms_magnesium", "category": "diet", "title": "마그네슘 보충 식단 가이드",
     "description": "PMS 부종·근육 긴장 완화를 돕는 마그네슘 함유 식품 가이드.", "target_contexts": ["pms"]},
    {"id": "cbt_pms_selfcompassion", "category": "cbt", "title": "자기 자비 3분 명상",
     "description": "PMS 감정 기복 시기에 자기 비난을 낮추는 짧은 CBT 기반 명상.", "target_contexts": ["pms"]},

    # Stress
    {"id": "ex_stress_breathing", "category": "exercise", "title": "호흡 중심 스트레칭",
     "description": "부교감신경 활성화를 위한 느린 호흡 결합 스트레칭.", "target_contexts": ["stress"]},
    {"id": "diet_stress_herbal", "category": "diet", "title": "카페인 대체 허브티 가이드",
     "description": "스트레스 급등 구간 카페인 과다 섭취를 줄이는 대체 음료 안내.", "target_contexts": ["stress"]},
    {"id": "cbt_stress_grounding", "category": "cbt", "title": "5-4-3-2-1 그라운딩 기법",
     "description": "급성 스트레스 반응을 낮추는 감각 기반 그라운딩 연습.", "target_contexts": ["stress"]},
    {"id": "cbt_stress_reframe", "category": "cbt", "title": "인지 재구성 저널링",
     "description": "스트레스 유발 생각을 기록하고 재구성하는 짧은 CBT 저널 프롬프트.", "target_contexts": ["stress"]},

    # Binge-eating risk
    {"id": "diet_binge_protein", "category": "diet", "title": "혈당 안정 단백질 간식",
     "description": "폭식 충동 시기 혈당을 안정시키는 고단백 간식 대안.", "target_contexts": ["binge"]},
    {"id": "cbt_binge_urge_surf", "category": "cbt", "title": "충동 서핑(Urge Surfing) 가이드",
     "description": "폭식 충동을 억누르지 않고 파도처럼 흘려보내는 CBT 기법.", "target_contexts": ["binge"]},
    {"id": "ex_binge_short_walk", "category": "exercise", "title": "5분 리셋 걷기",
     "description": "충동적 폭식 신호가 감지될 때 주의를 전환하는 짧은 걷기.", "target_contexts": ["binge"]},

    # Stable / general wellness
    {"id": "ex_stable_strength", "category": "exercise", "title": "난포기 고강도 근력 루틴",
     "description": "안정 구간에서 에스트로겐 상승을 활용한 고강도 근력 운동.", "target_contexts": ["stable"]},
    {"id": "diet_stable_balanced", "category": "diet", "title": "균형 잡힌 하루 식단 템플릿",
     "description": "특별한 위험 신호가 없는 평상시를 위한 일반 균형 식단.", "target_contexts": ["stable"]},
    {"id": "cbt_stable_gratitude", "category": "cbt", "title": "감사 저널 3줄 쓰기",
     "description": "컨디션이 안정적인 날의 정서 유지 습관.", "target_contexts": ["stable"]},
]


def items_for_context(risk_state: str):
    matches = [item for item in CONTENT_ITEMS if risk_state in item["target_contexts"]]
    if matches:
        return matches
    return [item for item in CONTENT_ITEMS if "stable" in item["target_contexts"]]


def get_item(content_id: str):
    for item in CONTENT_ITEMS:
        if item["id"] == content_id:
            return item
    return None
