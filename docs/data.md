# 데이터와 전처리

## 데이터 출처

| 분류 | 수집처 | 내부 테이블·파일 | 사용 내용 |
|---|---|---|---|
| KAU 장내거래 | KRX 배출권시장 | `raw.krx_ets_daily` | 거래일·종목별 시가, 종가, 고가, 저가, 거래량, 거래대금. 시장 VWAP와 거래량 계열 산출에 사용 |
| KAU 경매 | KRX 배출권 경매 결과 | `raw.krx_auction_monthly` | 경매 수량, 응찰 수량, 낙찰률, 참여자 수, 주문가격 계열 |
| 전력수급 | 전력통계정보시스템 EPSIS / KPX | `raw.epsis_power_supply_daily` | 최대수요, 최소수요, 공급능력, 예비력, 예비율 |
| SMP | 전력통계정보시스템 EPSIS / KPX | `raw.epsis_smp_monthly` | 전국·육지·제주 SMP |
| 발전연료비 | 전력통계정보시스템 EPSIS / KPX | `raw.epsis_fuel_cost_monthly` | 무연탄, 유연탄, LNG, 원자력, 유류 연료비·연료가격·열량단가 |
| 전력거래량 | 전력통계정보시스템 EPSIS / KPX | `raw.epsis_power_trade_volume_monthly` | 연료원별 발전·거래량과 시장/PPA 거래량 |
| 기상 | 기상청 KMA ASOS | `raw.kma_asos_weather_daily`, `raw.kma_asos_weather_station_daily` | 기온, 습도, 풍속, 강수, 일사, 일조, 냉난방도일 |
| EUA | EU ETS 시장 데이터 | `raw.eua_daily` | EUA 일별 가격·거래량 |
| 원유 | 국제 원유 시계열 | `raw.oil_daily` | WTI, Brent |
| 비원유 상품 | 국제 상품 시계열 | `raw.commodities_monthly` | LNG, 석탄, 유럽 천연가스 |
| 거시시장 | Yahoo Finance 및 KRX MDC | `raw.macro_indicators`, `raw.macro_market_indicator_daily` | KOSPI, S&P500, VIX, VKOSPI, 금, 금리, 환율 |
| GIR/공공 공시 | 온실가스종합정보센터 GIR 및 공공기관 공시 | `raw.gir_*`, `raw.kospo_*`, `raw.khnp_*`, `raw.kogas_*`, `raw.kwater_*` | 할당, 인증배출, 이월·차입, 공공기관 배출·할당 proxy |
| 검색·뉴스·정책 NLP | Naver DataLab, Naver News, GIR/환경부/KRX 공지, FinBERT 추론 결과 | `features/nlp_final/nlp_final_features.parquet`, `runpod_gpu_inference` | 검색 강도, 정책 관심도, 뉴스 tone, FinBERT 기사량 계열 |

## 분석 단위

분석 단위는 거래일(`trd_dd`)이다. KAU 여러 vintage가 같은 거래일에 거래되면 거래대금과 거래량을 합산해 시장 단위 가격을 만든다.

## Target

60일 horizon target은 시장 VWAP 로그수익률이다.

```text
target_logret_60d = log(future_vwap_60d) - log(market_vwap)
```

`market_vwap`은 같은 거래일의 모든 KAU vintage를 합산해 계산한다.

```text
market_vwap = sum(acc_trdval) / sum(acc_trdvol)
```

`future_vwap_60d`는 60 calendar-day 이후 첫 거래일의 시장 VWAP이다.

## 전처리

- 일별 자료는 거래일 기준으로 결합한다.
- 월별 자료는 해당 월 값의 공개 가능 시점을 기준으로 거래일에 붙인다.
- 정책·뉴스·검색 계열은 관측일 이후 사용 가능한 값만 붙인다.
- 결측치는 모델별 학습 파이프라인에서 처리하고, 결측률과 coverage는 feature manifest에 기록한다.
- 피처명은 짧은 영어 snake_case를 사용하고, 보고서용 표에는 한글 라벨을 함께 제공한다.

## 제외 기준

- `future_*`, `target_*`, `same_panel_*`, `pass_*` 계열은 target 생성 또는 평가 정보라 제외한다.
- 현재일 `mkt_market_vwap`, `mkt_log_market_vwap`는 target 산식의 현재 가격 항과 중복되어 제외한다.
- VWAP lag 피처는 과거 거래일 관측값이라 포함한다.
