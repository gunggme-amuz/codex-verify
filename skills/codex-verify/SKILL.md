---
name: codex-verify
description: |
  코드 수정이나 계획 작성이 완료되면 반드시 실행하는 크로스 모델 검증 스킬. 파일을 편집(Edit/Write)하거나 구현 계획을 작성한 직후, 사용자의 별도 요청 없이도 자동으로 OpenAI Codex CLI를 통해 독립적인 코드 리뷰, 버그 탐지, 보안 점검, 테스트 검증을 수행한다. 구조화된 JSON 파싱, 라운드별 델타 추적, HTML/MD 리포트, 프로젝트별 커스텀 룰을 지원한다. 코드를 수정했으면 이 스킬을 사용한다. 계획을 세웠으면 이 스킬을 사용한다. 리팩토링, 새 파일 생성, 버그 수정 등 어떤 코드 변경이든 이 스킬을 트리거한다. "검증해줘", "codex로 체크", "리포트 생성", "검증 훅 설치" 요청에도 사용한다.
---

# Codex Verify v2: Cross-Model Verification

## Overview

이 스킬은 OpenAI Codex CLI를 독립적인 검증자로 활용한다. Claude가 작성한 코드를 다른 모델(Codex)이 검증함으로써 단일 모델의 편향과 맹점을 보완한다. 리서치에 따르면 멀티모델 검증은 단일 모델 대비 약 50% 더 많은 버그를 탐지한다.

v2는 프롬프트 템플릿을 넘어, 구조화된 파이프라인을 제공한다:
- **구조화 파싱**: Codex 출력을 JSON으로 변환하여 결정적(deterministic) 판단
- **델타 추적**: 라운드간 해결/신규 이슈 비교
- **프로젝트 설정**: `.codex-verify.yml`로 커스텀 룰과 검증 기준 조정
- **리포트**: HTML/MD 형식의 검증 히스토리 리포트
- **Git Hook**: pre-commit에서 자동 검증

## Prerequisites

- `codex` CLI 설치 필요 (`npm i -g @openai/codex` 또는 `brew install --cask codex`)
- OpenAI 인증 완료 (API key 또는 ChatGPT 로그인)
- Python 3.8+

## Scripts Location

이 스킬의 스크립트는 SKILL.md가 위치한 디렉토리의 `../../scripts/` 에 있다. 스킬이 트리거되면, 먼저 이 SKILL.md 파일의 절대 경로를 확인하고, 그 경로에서 `../../scripts/`로 이동하여 스크립트 디렉토리의 절대 경로를 결정한다.

예시: SKILL.md가 `/path/to/codex-verify/skills/codex-verify/SKILL.md`에 있으면, 스크립트는 `/path/to/codex-verify/scripts/`에 있다.

이하 `{scripts}` 는 이 스크립트 디렉토리의 절대 경로를 의미한다.

## Verification Types

| Type | Description |
|------|-------------|
| `code-review` | 정확성, 보안, 성능, 가독성 점검 |
| `test-verify` | 테스트 실행, 커버리지, 누락 엣지케이스 확인 |
| `plan-verify` | 계획의 실현가능성, 완전성, 의존성 평가 |
| `security-check` | OWASP Top 10 보안 취약점 탐지 |

## Execution Pipeline

### Step 0: Load Configuration

```bash
python3 {scripts}/load_config.py --project-dir {project_dir}
```

JSON 출력을 읽고, 이후 모든 단계에서 이 설정을 사용한다. `.codex-verify.yml`이 없으면 기본값이 적용된다. 설정 스키마는 `references/config-schema.md`를 참조.

주요 설정:
- `max_rounds`: 최대 검증 반복 (기본 3)
- `severity_threshold`: "FAIL" 또는 "WARN" (루프 재진입 기준)
- `custom_rules`: 프로젝트별 검증 기준 (Codex 프롬프트에 주입)
- `ignore_patterns`: 검증 제외 파일 패턴
- `language`: 프롬프트 언어 (ko/en)

### Step 1: Identify Targets

검증 대상 파일을 파악한다:
- `git diff --name-only`로 변경 파일 확인
- `git status`로 신규 파일 확인
- 설정의 `ignore_patterns`에 해당하는 파일은 제외

### Step 2: Build Verification Prompt

검증 유형과 설정에 따라 프롬프트를 구성한다.

#### 코드 리뷰 프롬프트 (language: ko)
```
다음 파일들을 리뷰해줘: {파일목록}

다음 관점에서 검토하고, 각 항목별로 [PASS], [WARN], [FAIL] 태그를 붙여서 결과를 알려줘:

1. 정확성: 로직 오류, 오프바이원 에러, null/undefined 처리
2. 보안: 인젝션, XSS, 하드코딩된 시크릿, 안전하지 않은 디시리얼라이제이션
3. 성능: 불필요한 반복, N+1 쿼리, 메모리 누수 패턴
4. 엣지 케이스: 빈 입력, 극단값, 동시성 문제
5. 코드 품질: 네이밍, 중복, 단일 책임 원칙

{custom_rules가 있으면 추가:}
추가 검증 기준:
- {rule 1}
- {rule 2}
...

문제가 없으면 "ALL CLEAR"라고 명시해줘.
```

#### Code Review Prompt (language: en)
```
Review these files: {file_list}

Check each aspect and tag findings as [PASS], [WARN], or [FAIL]:

1. Correctness: logic errors, off-by-one, null handling
2. Security: injection, XSS, hardcoded secrets, unsafe deserialization
3. Performance: unnecessary loops, N+1 queries, memory leaks
4. Edge cases: empty input, boundary values, concurrency
5. Code quality: naming, duplication, single responsibility

{if custom_rules exist:}
Additional rules:
- {rule 1}
- {rule 2}
...

If no issues found, state "ALL CLEAR".
```

#### 테스트 검증 / 계획 검증 / 보안 점검
각 유형에 맞는 프롬프트를 구성한다. 핵심은 동일: 항목별 [PASS]/[WARN]/[FAIL] 태그 + ALL CLEAR 규칙.

### Step 3: Execute Codex

```bash
codex exec "{prompt}" 2>/dev/null > /tmp/codex_verify_raw_$$.txt
```

- 타임아웃: 설정의 `timeout` 값 (기본 300초)
- stderr 억제 (진행상황 출력)
- 결과는 임시 파일에 저장

### Step 4: Parse Result (구조화 파싱)

```bash
python3 {scripts}/parse_result.py \
  --raw-file /tmp/codex_verify_raw_$$.txt \
  --round {현재_라운드} \
  --type {verify_type} > /tmp/codex_verify_parsed_$$.json
```

JSON 출력 구조:
```json
{
  "verdict": "FAIL",
  "counts": {"PASS": 3, "WARN": 1, "FAIL": 2},
  "items": [
    {"tag": "FAIL", "category": "보안", "detail": "SQL 인젝션 취약점", "files": ["api.py"]}
  ],
  "delta": null
}
```

이 JSON의 `verdict`와 `counts`로 루프 결정을 한다. 텍스트를 직접 파싱하지 않는다.

### Step 5: Track History (히스토리 누적)

```bash
python3 {scripts}/generate_report.py \
  --add-result /tmp/codex_verify_parsed_$$.json \
  --project-dir {project_dir}
```

`.codex-verify-history.json`에 결과를 누적하고, 이전 라운드 대비 델타를 자동 계산한다:
- resolved: 이전에 있다가 해결된 이슈 수
- new_issues: 새로 발견된 이슈 수
- FAIL/WARN/PASS 변화량

### Step 6: Loop Decision (검증 루프)

파싱된 JSON 결과에 기반하여 루프를 관리한다.

#### 루프 진입 조건
- `verdict`가 "FAIL"일 때
- `severity_threshold`가 "WARN"이고 `verdict`가 "WARN"일 때

#### 루프 내 동작
1. 이슈를 사용자에게 간결하게 보고 (아래 형식)
2. FAIL 항목을 수정
3. Step 3부터 재실행

#### 루프 상태 보고 형식

```
[검증 라운드 {N}/{max_rounds}]
- PASS: {count}개 항목
- WARN: {count}개 항목
- FAIL: {count}개 항목
- 델타: {resolved}개 해결, {new_issues}개 신규
→ {판정 메시지}
```

#### 루프 탈출 조건 (하나라도 만족하면 종료)

| # | Condition | Check |
|---|-----------|-------|
| 1 | ALL CLEAR | `all_clear == true` |
| 2 | Max rounds | `round >= config.max_rounds` |
| 3 | No progress | 이전 라운드와 동일한 FAIL items (detail 기준 2회 연속) |
| 4 | No FAILs | `counts.FAIL == 0` (severity_threshold가 FAIL일 때) |
| 5 | User abort | 사용자가 "그만", "충분해", "skip" 등을 말함 |
| 6 | Codex error | codex exec 실패 (재시도 1회 후에도 실패) |

### Step 7: Final Report (최종 리포트)

검증 완료 후 리포트를 생성한다:

```bash
python3 {scripts}/generate_report.py \
  --report --format {config.report_format} \
  --project-dir {project_dir}
```

- `md` 포맷: 마크다운을 인라인으로 표시
- `html` 포맷: `.codex-verify-report.html` 생성 후 경로를 사용자에게 안내

### Cleanup

검증 완료 후 임시 파일을 정리한다:
```bash
rm -f /tmp/codex_verify_raw_$$.txt /tmp/codex_verify_parsed_$$.json
```

## Additional Commands

사용자가 명시적으로 요청할 때 사용:

### Report Generation
사용자가 "리포트 보여줘", "검증 히스토리" 등을 말하면:
```bash
python3 {scripts}/generate_report.py --report --format html --project-dir {project_dir}
```

### Git Hook Installation
사용자가 "훅 설치", "pre-commit 설정" 등을 말하면:
```bash
python3 {scripts}/install_hook.py --project-dir {project_dir}
```

### Configuration
사용자가 "검증 설정" 등을 말하면 `references/config-schema.md`를 참조하여 `.codex-verify.yml` 생성을 도움.

## Important Principles

1. **Codex는 보조 도구이지 최종 판단자가 아니다.** Codex의 false positive가 가능하므로, 각 FAIL 항목의 타당성을 Claude가 먼저 판단한 뒤 수정한다. 맹목적 수정 금지.

2. **사용자의 시간을 존중한다.** 사소한 스타일 이슈로 루프를 돌리지 않는다. FAIL만 자동 수정 대상이며, WARN은 보고만 한다 (severity_threshold가 WARN이 아닌 한).

3. **투명하게 동작한다.** Codex에 보내는 프롬프트와 파싱된 JSON 결과를 사용자가 확인할 수 있게 한다.

4. **컨텍스트를 전달한다.** 검증 프롬프트에 기술 스택, 프레임워크 정보를 포함하면 정확도가 올라간다. custom_rules도 이 목적에 활용한다.
