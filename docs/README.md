# FEMS Mermaid Diagrams

이 폴더는 FEMS pre-model pipeline skeleton의 Mermaid diagram을 파일별로 보관한다.

GitHub에서는 `.md` 파일의 Mermaid block이 바로 렌더링된다. `.mmd` 파일은 Mermaid CLI, 문서 변환, 이미지 렌더링용 원본이다.

## Diagram files

| Diagram | GitHub render | Mermaid source |
|---|---|---|
| 전체 pipeline | [`01_pre_model_pipeline.md`](01_pre_model_pipeline.md) | [`01_pre_model_pipeline.mmd`](01_pre_model_pipeline.mmd) |
| Latency-aware sequence | [`02_latency_sequence.md`](02_latency_sequence.md) | [`02_latency_sequence.mmd`](02_latency_sequence.mmd) |
| Chat routing skeleton | [`03_chat_routing.md`](03_chat_routing.md) | [`03_chat_routing.mmd`](03_chat_routing.mmd) |
| Airflow report skeleton | [`04_airflow_report.md`](04_airflow_report.md) | [`04_airflow_report.mmd`](04_airflow_report.mmd) |

## Optional local render

Mermaid CLI가 설치되어 있으면 다음처럼 이미지로 렌더링할 수 있다.

```bash
mmdc -i docs/specs/diagrams/01_pre_model_pipeline.mmd -o docs/specs/diagrams/01_pre_model_pipeline.svg
mmdc -i docs/specs/diagrams/02_latency_sequence.mmd -o docs/specs/diagrams/02_latency_sequence.svg
mmdc -i docs/specs/diagrams/03_chat_routing.mmd -o docs/specs/diagrams/03_chat_routing.svg
mmdc -i docs/specs/diagrams/04_airflow_report.mmd -o docs/specs/diagrams/04_airflow_report.svg
```

현재 repository에는 SVG 산출물을 commit하지 않는다. Mermaid source와 GitHub-renderable Markdown만 추적한다.
