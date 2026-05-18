# 모델링 소스 정리

## 주력 모델

주력 모델은 VMD-GARCH-LSTM 하나로 정리한다.

- 입력 피처: selected 125
- 검증 방식: 28-fold expanding walk-forward
- 모델 구조: VMD decomposition, GARCH, LSTM/LSTM-Attention, nonlinear ensemble
- 성능 요약표: `outputs/tables/models/main_table.csv`
- Shard별 검증표: `outputs/tables/models/shards.csv`
- Fold별 상세표: `outputs/tables/vmd/by_fold.csv`
- 예측값 표: `outputs/tables/vmd/pred.csv`
- 시각화: `outputs/figures/vmd/`
- 재현 코드: `scripts/vmd.py`
- 추적 코드: `scripts/track.py`

보고서와 발표에서는 모델명을 VMD-GARCH-LSTM으로 표기한다. 내부 실행 식별자는 발표용 표와 그림에 노출하지 않는다.

## 검증 지표

- RMSE
- MAE
- WAPE
- R²
- Hit rate
- Balanced accuracy
- Macro F1
- Correlation
- IC
