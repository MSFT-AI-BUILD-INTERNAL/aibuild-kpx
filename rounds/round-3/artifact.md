## Recommendation

벤치마크를 더 좋게 만드는 핵심은 "더 많은 샘플"보다 "다른 실패 모드를 보는 샘플"이다. 지금 kpx는 prompt compression의 token 효과를 잘 재지만, 실제 워크플로에서 중요한 도구 호출, 장문 컨텍스트, patch-level 수정 난이도는 충분히 분리되어 있지 않다.

### Actions
1. `T08_patch.json`: 간단한 repo patch + test pass/fail 과제 추가.
2. `T09_tool_use.json`: schema-heavy tool call / JSON contract / retrieval-limited task 추가.
3. `T10_long_context.json`: 긴 문맥에서 `tokens saved -> extra evidence retained` 효과 측정.
4. `T11_locale.json`: mixed-language, locale formatting, region-specific instruction tasks 추가.
5. 뷰에 `family coverage`, `family-weighted score`, `worst-family delta`를 노출한다.

### Why this matters
- 토큰 절감은 목적이 아니라 더 중요한 정보를 컨텍스트에 넣기 위한 수단이다.
- 현실적 task family가 늘어나야 token reduction과 utility preservation의 균형을 제대로 볼 수 있다.

### Source notes
- SWE-bench Verified: real issue + execution realism.
- SWE-bench Multilingual: 언어/생태계 편향 노출.
- Anthropic workflows: task routing과 분리된 전문 평가 축의 가치.