# 보고서 작성 소스

## Ⅰ. 과제 개요 및 가설

사용 자료: `data.md`, `features.md`

작성 재료:
- KAU 가격 예측 target 정의
- 전력수급, 연료비, SMP, 날씨, 경매, 시장 미시구조, 외부시장, 정책·NLP 변수군
- 변수군별 가격 영향 가설

## Ⅱ. 분석 환경 및 데이터

사용 자료: `env.md`, `data.md`, `features.md`, `requirements.txt`

작성 재료:
- 패키지 버전
- 데이터 출처
- VWAP와 target 산식
- baseline/selected 피처 수
- selected 피처 전체 정의와 라벨
- 누수 제외 기준

## Ⅲ. 분석 방법 및 모델링

사용 자료: `models.md`, `summary.csv`, `by_fold.csv`, `decision.csv`

작성 재료:
- 모델군 구성
- walk-forward 검증 방식
- Optuna 탐색
- IC, correlation, 방향성, error, fold 안정성 지표

## Ⅳ. 인사이트 및 해결책

사용 자료: `best_objective.csv`, `best_ic.csv`, `best_direction.csv`, `decision.csv`

작성 재료:
- ranking 성능이 좋은 모델
- 방향성 판단에 유리한 모델
- 안정성이 낮아 보조로만 둘 모델
- feature group별 해석

## Ⅴ. 정책 활용 및 기대효과

사용 자료: `decision.csv`, `features.md`, `by_fold.csv`

작성 재료:
- 조달 타이밍 판단 보조
- 시장 위험 조기 경보
- 정책·전력·경매 변수 모니터링
- 모델 자동화 시 업무 단축 가능 지점
- 민원, 법적 제약, AI 편향성, 데이터 지연 리스크
