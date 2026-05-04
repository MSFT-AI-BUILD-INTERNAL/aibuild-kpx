## Round 3 — Coverage Expansion (Languages / Tool Use / Task Realism)

### Goal
현재 벤치마크가 놓치는 실제 사용 장면을 늘린다.

### Local evidence
- 현재 task set은 coding, docs, JSON, safety, translation 중심이다.
- README 기준 deep code / model compare는 강하지만, 도구 사용, 장기 문맥, 실제 patch-level realism은 아직 약하다.

### External evidence
- SWE-bench Verified는 real GitHub issue 기반 execution benchmark를 표준 비교축으로 만든다.
- SWE-bench Multilingual은 9개 언어와 42개 저장소로 범위를 넓혀 모델 편향을 드러낸다.
- Anthropic은 routing과 orchestrator-workers를 복잡한 입력에서 분리된 평가 축으로 본다.

### Proposed change set
1. patch-level coding tasks를 추가해 `issue -> edit -> tests` 흐름을 측정한다.
2. tool-use / retrieval / schema-heavy tasks를 별도 트랙으로 분리한다.
3. translation 외 i18n을 넘어서 mixed-language prompts와 locale-specific formatting을 추가한다.
4. long-context tasks를 넣어 token saving이 실제로 더 많은 useful context를 담는지 본다.
5. pass rate 외 `coverage by task family`를 공개한다.

### Cheap validation
- 새 트랙 3종을 각 5~10문항 파일로 만들고 뷰에서 family별 집계가 나오는지 확인.