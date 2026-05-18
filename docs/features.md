# 피처 정의

## 피처셋 개요

| 피처셋 | 피처 수 | 설명 |
|---|---:|---|
| baseline | 222 | 비교 기준 피처셋 |
| selected | 125 | 최종 모델 입력 피처셋 |

## selected 그룹별 개수

| 그룹                  |   개수 |
|:----------------------|-------:|
| power_energy          |     30 |
| market_microstructure |     25 |
| external_market       |     16 |
| nlp                   |     10 |
| weather               |      9 |
| auction               |      7 |
| pwr                   |      6 |
| ext                   |      5 |
| mkt                   |      5 |
| fuel                  |      4 |
| policy_compliance     |      2 |
| wx                    |      2 |
| src                   |      2 |
| pol                   |      1 |
| nlp_finbert           |      1 |

## selected 피처 전체 정의

아래 표는 현재 `selected_feature_matrix.parquet`에 정의된 모든 selected 피처와 한글 라벨이다.

| 피처명                                | 라벨                      | 그룹                  |
|:--------------------------------------|:--------------------------|:----------------------|
| mkt_vol_ma60                          | 거래량 이동평균           | market_microstructure |
| fuel_anth_krwkwh                      | 무연탄 단가               | power_energy          |
| pwr_peak_dem_mw                       | 최대 전력수요             | power_energy          |
| pwr_coal_gas_gwh                      | 석탄가스 발전량           | power_energy          |
| pwr_hydro_gwh                         | 수력 발전량               | power_energy          |
| pwr_mkt_tot_gwh                       | 총 전력시장 거래량        | power_energy          |
| pwr_nuke_gwh                          | 원자력 발전량             | power_energy          |
| pwr_wind_gwh                          | 풍력 발전량               | power_energy          |
| pwr_smp_jeju_krwkwh                   | 계통한계가격              | power_energy          |
| wx_nat_cdd18                          | 전국 냉방도일             | weather               |
| wx_nat_hdd18                          | 전국 난방도일             | weather               |
| fuel_heat_lng_krwgcal                 | LNG 열량단가              | power_energy          |
| wx_stn_min_temp_c                     | 관측소 최저기온           | weather               |
| wx_stn_avg_rh                         | 관측소 평균습도           | weather               |
| mkt_daily_logret                      | 시장 일간 로그수익률      | market_microstructure |
| mkt_logret_lag1                       | 시장 수익률 시차          | market_microstructure |
| mkt_logret_lag5                       | 시장 수익률 시차          | market_microstructure |
| mkt_logret_ma20                       | 시장 수익률 이동평균      | market_microstructure |
| mkt_logret_ma5                        | 시장 수익률 이동평균      | market_microstructure |
| mkt_logret_ma60                       | 시장 수익률 이동평균      | market_microstructure |
| mkt_logret_vol_20d                    | 시장 수익률 변동성        | market_microstructure |
| mkt_vol                               | 거래량                    | market_microstructure |
| mkt_vol_lag1                          | 거래량 시차               | market_microstructure |
| mkt_vol_lag20                         | 거래량 시차               | market_microstructure |
| mkt_vol_lag5                          | 거래량 시차               | market_microstructure |
| mkt_vol_lag60                         | 거래량 시차               | market_microstructure |
| mkt_vol_ma20                          | 거래량 이동평균           | market_microstructure |
| mkt_vol_ma5                           | 거래량 이동평균           | market_microstructure |
| mkt_vol_std20                         | 거래량 변동성             | market_microstructure |
| mkt_vol_std60                         | 거래량 변동성             | market_microstructure |
| fuel_oil_krwkwh                       | 유류 연료비               | power_energy          |
| fuel_bitum_coal_krwton                | 유연탄 가격               | power_energy          |
| pwr_day                               | 전력수급 기준일           | power_energy          |
| pwr_sup_cap_mw                        | 전력 공급능력             | power_energy          |
| pwr_anth_gwh                          | 무연탄 발전량             | power_energy          |
| pwr_bitum_coal_gwh                    | 유연탄 발전량             | power_energy          |
| pwr_ocean_gwh                         | 해양 발전량               | power_energy          |
| pwr_oil_gwh                           | 유류 발전량               | power_energy          |
| pwr_other_gwh                         | 기타 발전량               | power_energy          |
| pwr_pumped_storage_gwh                | 양수 발전량               | power_energy          |
| pwr_solar_gwh                         | 태양광 발전량             | power_energy          |
| wx_nat_is_precip_day                  | 강수 발생 여부            | weather               |
| wx_nat_precip_mm                      | 전국 강수량               | weather               |
| wx_stn_sunshine_hours                 | 관측소 일조시간           | weather               |
| ext_us10y_z60                         | 미국 10년물 금리          | external_market       |
| ext_us10y_chg20                       | 미국 10년물 금리          | external_market       |
| ext_kr10y_chg20                       | 한국 10년물 금리          | external_market       |
| ext_kr10y_z60                         | 한국 10년물 금리          | external_market       |
| ext_sp500_z60                         | S&P500                    | external_market       |
| ext_vkospi_z60                        | VKOSPI                    | external_market       |
| ext_gold_z60                          | 금 가격                   | external_market       |
| ext_gold_ret20                        | 금 가격                   | external_market       |
| ext_vkospi_chg20                      | VKOSPI                    | external_market       |
| fx_usdkrw_ret20                       | 원/달러 환율              | external_market       |
| ext_kospi_z60                         | KOSPI                     | external_market       |
| fx_usdkrw_z60                         | 원/달러 환율              | external_market       |
| ext_kospi_ret20                       | KOSPI                     | external_market       |
| ext_sp500_ret20                       | S&P500                    | external_market       |
| ext_vix_z60                           | VIX                       | external_market       |
| ext_vix_chg20                         | VIX                       | external_market       |
| pol_comp_attn                         | 이행마감 관심도           | policy_compliance     |
| pol_comp_deadline_w                   | 이행마감 가중치           | policy_compliance     |
| search_kau_intensity_level            | KAU 검색 관심도           | nlp                   |
| search_kau_intensity_shock            | KAU 검색 관심도           | nlp                   |
| search_kau_intensity_percentile_60d   | KAU 검색 관심도           | nlp                   |
| search_kau_intensity_ratio_20d        | KAU 검색 관심도           | nlp                   |
| gov_policy_tightening_index           | 정부 정책 긴축지수        | nlp                   |
| gov_compliance_policy_attention       | 정부 이행정책 관심도      | nlp                   |
| news_text_tightening_minus_easing_60d | 뉴스 긴축-완화 tone       | nlp                   |
| news_text_tightening_minus_easing_30d | 뉴스 긴축-완화 tone       | nlp                   |
| fuel_lng_japan                        | LNG 가격                  | fuel                  |
| fuel_natgas_europe                    | 천연가스 가격             | fuel                  |
| fuel_coal_newcastle                   | 석탄 가격                 | fuel                  |
| pwr_fuel_price_anthracite_krw_pe      | 무연탄 연료가격           | pwr                   |
| pwr_fuel_cost_nuclear_krw_per_kw      | 원자력 연료비             | pwr                   |
| pwr_minimum_demand_mw                 | 최소 전력수요             | pwr                   |
| pwr_trade_volume_ppa_total_gwh        | PPA 전력거래량            | pwr                   |
| ext_lpr                               | EUA 저가                  | ext                   |
| ext_acc_trdvol                        | EUA 누적거래량            | ext                   |
| pol_no_5                              | 인증배출 순번 proxy       | pol                   |
| wx_avg_wind_speed_mps                 | 평균풍속                  | wx                    |
| wx_solar_radiation_mj_m2              | 일사량                    | wx                    |
| src_period_2                          | 제도 기간 proxy           | src                   |
| src_intensity                         | 배출/발전 intensity       | src                   |
| mkt_clsprc                            | 종가                      | mkt                   |
| mkt_chgh                              | 전일 대비 가격변화        | mkt                   |
| mkt_opr                               | 시가                      | mkt                   |
| mkt_acc_trdval                        | 누적 거래대금             | mkt                   |
| ext_kospi                             | KOSPI                     | ext                   |
| ext_value                             | 거시시장 지표값           | ext                   |
| fuel_wti                              | WTI 유가                  | fuel                  |
| nlp_finbert_count_60d                 | FinBERT 기사 수 60일 합계 | nlp_finbert           |
| wx_stn_max_temp_c                     | 관측소 최고기온           | weather               |
| compliance_deadline_calendar_weight   | 이행마감 달력가중치       | nlp                   |
| compliance_deadline_attention         | 이행마감 관심도           | nlp                   |
| pwr_renewable_total_gwh               | 재생에너지 총 발전량      | power_energy          |
| pwr_installed_capacity_mw             | 전력 설비용량             | pwr                   |
| pwr_trade_volume_fuel_cell_gwh        | 연료전지 전력거래량       | pwr                   |
| pwr_bio_gwh                           | 바이오 발전량             | power_energy          |
| pwr_market_ppa_total_gwh              | 시장·PPA 총 전력거래량    | power_energy          |
| ext_usdkrw                            | 원/달러 환율              | ext                   |
| pwr_lng_gwh                           | LNG 발전량                | power_energy          |
| pwr_resv_cap_mw                       | 전력 예비력               | power_energy          |
| pwr_resv_mgn_pct                      | 전력 예비율               | power_energy          |
| mkt_vol_log1p                         | 로그 거래량               | market_microstructure |
| mkt_acc_trdvol                        | 누적거래량                | mkt                   |
| pwr_waste_gwh                         | 폐기물 발전량             | power_energy          |
| auc_trdcnt                            | 경매 체결건수             | auction               |
| auc_part_cnt                          | 경매 참여자수             | auction               |
| auc_trd_qty                           | 경매 거래수량             | auction               |
| auc_trd_rto                           | 경매 낙찰률               | auction               |
| auc_appl_qty                          | 경매 응찰수량             | auction               |
| auc_hgst_ord_prc                      | 경매 최고 주문가격        | auction               |
| auc_lwst_ord_prc                      | 경매 최저 주문가격        | auction               |
| mkt_n_vintages                        | 거래 vintage 수           | market_microstructure |
| mkt_is_blended                        | 복수 vintage 거래 여부    | market_microstructure |
| mkt_vwap_range                        | vintage 간 VWAP 범위      | market_microstructure |
| pwr_smp_total_krwkwh                  | 통합 SMP                  | power_energy          |
| pwr_smp_land_krwkwh                   | 육지 SMP                  | power_energy          |
| fuel_lng_krwkwh                       | LNG 연료비                | power_energy          |
| wx_stn_cdd18                          | 관측소 냉방도일           | weather               |
| mkt_vwap_lag1                         | 시장 VWAP 1일 시차        | market_microstructure |
| mkt_vwap_lag5                         | 시장 VWAP 5일 시차        | market_microstructure |
| mkt_vwap_lag20                        | 시장 VWAP 20일 시차       | market_microstructure |
| mkt_vwap_lag60                        | 시장 VWAP 60일 시차       | market_microstructure |

## 제외 기준

현재일 시장 VWAP level 피처인 `mkt_market_vwap`, `mkt_log_market_vwap`는 target 산식의 현재 가격 항과 중복되므로 selected에 포함하지 않는다.
`future_*`, `target_*`, `same_panel_*`, `pass_*` 계열은 target 생성 또는 평가 정보이므로 selected에 포함하지 않는다.
VWAP lag 피처는 과거 거래일의 관측값이므로 selected에 포함한다.
