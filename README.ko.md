<div align="center">

# longgraph

**Claude Code, Cursor, Codex, Grok Build를 위한 장기 실행 에이전트 스킬**

지속적인 원장, 클린 컨텍스트 슈퍼바이저, 검증된 게이트로 에이전트 드리프트를 중지하세요.
하나의 루프에 많은 장기 작업을 큐에 넣고(관련 없는 작업도 가능), 호스트를 전환한 후에도
파일에 대해 동일한 프롬프트를 재전송하여 계속 진행할 수 있습니다.

한 번 설계 → 지속적인 루프 그래프 컴파일 → 완료까지 모두 검증.

[![GitHub stars](https://img.shields.io/github/stars/levi-qiao/longgraph-skill?style=flat-square&color=6C63FF)](https://github.com/levi-qiao/longgraph-skill/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-14B8A6?style=flat-square)](LICENSE)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-22C55E?style=flat-square)](CONTRIBUTING.md)
![Hosts: Claude Code · Cursor · Codex · Grok Build](https://img.shields.io/badge/Hosts-Claude%20Code%20·%20Cursor%20·%20Codex%20·%20Grok%20Build-111827?style=flat-square)
![Type: agent skill · prompt library](https://img.shields.io/badge/Type-agent%20skill%20·%20prompt%20library-0EA5E9?style=flat-square)

[English](README.md) · [日本語](README.ja.md) · 한국어

</div>

<img alt="Executor and clean-context supervisor loops running side by side" src="assets/graph.png" width="100%" />

## 📌 이 포크에 대하여

이것은 [Samek86](https://github.com/Samek86)이 유지 관리하는 [levi-qiao/longgraph-skill](https://github.com/levi-qiao/longgraph-skill)의 **개선된 포크**입니다.

### 🎯 추가 기능

- **📚 다국어 문서화**: 영어, 일본어, 한국어로 된 완전한 README
- **📊 깊은 status.json 연결**: 실시간 실행 아티팩트가 머신 리더블 진행 상황(`status.json`)을 방출 — 노드가 자동으로 페이즈, 라운드, 하트비트를 업데이트; 헬퍼 스크립트 + CI 검증 포함
- **🔍 Scout 자동 브리프 라이프사이클**: 프리셋 핫 패스의 Scout 노드 — 컴파일러가 크리티컬 패스 외부 조사를 위해 Scout 브리프 + findings 프로토콜을 자동 생성 (loop-research / loop-deliver / loop-converge)
- **🔒 비밀 스크럽**: 커밋 전에 비밀 정보를 스캔하는 로컬 스크립트
- **✅ CI 검증**: GitHub Actions를 통한 자동 구조 및 링크 검증

> **업스트림과의 호환성**: 모든 개선 사항은 추가적입니다. 핵심 loop-graph 설계는 변경되지 않았습니다.
> 자세한 내용은 [FORK.md](FORK.md)를 참조하세요.

---

## longgraph란?

**longgraph**(`longgraph-skill`)는 **장기 실행/장기 수평선** 에이전트 작업을 위한 큐레이션된 **에이전트 스킬** 및 크로스 호스트 **프롬프트 라이브러리**입니다. 수시간에 걸친 코딩, 멀티 마일스톤 마이그레이션, **하나의 루프에서 장기 작업 큐**(관련이 있을 필요는 없음), 그리고 하나의 컨텍스트 윈도우를 초과하여 계속되는 모든 작업에 대응합니다. 이것은 **에이전트를 위한 그래프 엔지니어링**입니다: 전문화된 역할(executor · supervisor · scout)이 지속적이고 검사 가능한 파일을 통해 연결됩니다—다른 오케스트레이션 런타임이 아닙니다. 스코어보드가 디스크에 존재하기 때문에 **실행 중에 호스트를 변경**할 수 있습니다: 동일한 워크스페이스를 열고, 동결된 노드 프롬프트를 재전송하고, 계속하세요.

> **하나의 지속적인 그래프, 호스트 간 이식 가능.** 간단한 자체 완결형 목표의 경우, 호스트의 일반 작업 또는 목표를 직접 사용하세요. longgraph는 지속적인 그래프 구조가 가치를 추가하는 곳에서 시작됩니다.

## 증거

이것들은 원샷 데모가 아닙니다. longgraph는 **Markdown 스킬/프롬프트 라이브러리**(오케스트레이션 런타임이 아님)입니다. 표는 **검증 가능한 공개 Git**, **기능만 편집된 멀티데이 패턴**, 그리고 **합성 교재**를 혼합합니다.

| 사례 | 독자가 검증할 수 있는 것 | 종류 |
| --- | --- | --- |
| [**이 스킬의 자체 반복**](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md) | **약 14 달력일**(2026-07-19 → 2026-08-02)에 걸친 **87**개의 공개 커밋, **74**개 파일, 라이브러리에 다시 작성된 메소드 규칙(웨이크 엣지 없음, 게이트 대기 백로그, 차단≠파크, 제한된 라이브 엣지, 저작≠런타임) | 공개 Git 사실—고정 앵커 `6efcb7f` |
| [**멀티데이 컨트롤 플레인 패턴**](skills/loop-graph/examples/redacted-multiday-control-plane/README.md) | 멀티데이 월클락, 수십 라운드, 많은 지시사항: 지속적인 원장, 클린 컨텍스트 슈퍼바이저가 자체 보고된 증거를 뒤집음, 건너뛸 수 없는 게이트, 차단된 작업 레인, 소유자 A/B/C—**기능만**, 개인 페이로드 없음 | 편집된 실제 실행 패턴 |
| [**migrate-blob-storage**](skills/loop-graph/examples/migrate-blob-storage/README.md) | 멀티 마일스톤 원장: 파일럿→코호트, 강제 수렴, 슈퍼바이저가 자체 보고된 증거를 뒤집음, 건너뛸 수 없는 게이트+차단된 작업 레인 | 합성 교재(가상 앱) |
| [**add-tests-to-cli**](skills/loop-graph/examples/add-tests-to-cli/README.md) | 가장 작은 전체 실행: 3라운드, 등록 후 연기, 클린 컨텍스트 슈퍼바이저 의도 | 합성 교재(가상 CLI) |

**시계 읽기.** 자체 반복 윈도우의 약 14일/약 340시간은 **프로젝트 월클락**(첫 공개 커밋→고정 앵커)이며, 연속적인 모델 실행이 아니며 무인 프로덕션 자율성 주장도 아닙니다. [자체 반복 사례](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md)의 명령으로 Git를 재확인하세요. 편집된 멀티데이 카드는 **거친 버킷만** 사용하며 개인 Git 재확인 **가능하지 않습니다**—그 증거 경계를 참조하세요.

향후 사례의 공개 규칙: [공개/개인 경계](docs/public-private-boundary.md).

## 언제 사용할까요?

다음 중 하나가 필요한 경우 longgraph에 손을 뻗으세요:

- 컨텍스트 압축/세션 재설정 후에도 계속 작동하는 **장기 수평선 에이전트**
- 채팅 메모리 진행 상황 대신 **지속적인 작업 원장**(단일 스코어보드)
- **하나의 루프에서 여러 장기 작업**—항목이 관련 없더라도 지속적인 큐
- **호스트 이식 가능 연속성**—파일에 대해 프롬프트를 재전송하여 실행 중에 Claude Code ↔ Cursor ↔ Codex ↔ Grok Build 전환
- 독립적인 **클린 컨텍스트 슈퍼바이저**—같은 에이전트가 자신을 평가하는 것이 아님
- **검증된 완료**: 수용 게이트가 실제 출력에 대해 재실행되며, 자체 보고 "완료"가 아님
- **건너뛸 수 없는 게이트**와 명시적인 소유자 레드 라인이 있는 멀티 마일스톤 작업
- **Claude Code · Cursor · Codex · Grok Build**에서 작동하는 **Markdown 스킬/프롬프트 라이브러리**

### 언제 사용하지 *말아야* 할까요?

- 원샷 편집, 작은 PR 크기 작업, 또는 단일 클린 세션에 맞는 것
- **런타임 프레임워크**가 필요한 경우(LangGraph, CrewAI, AutoGen, 커스텀 에이전트 서버)
- 원장, 게이트 또는 독립적인 리뷰가 필요하지 않은 단일 짧은 프롬프트만 필요한 경우

### 비교

| 접근 방식 | 런타임/서버? | 독립 검증자 | 지속적인 스코어보드 | 멀티태스크 큐+실행 중 호스트 전환 |
| --- | --- | --- | --- | --- |
| LangGraph / CrewAI / AutoGen | 예 | 직접 구축 | 일반적으로 예 | 프레임워크 종속; 종종 단일 배포 스택 |
| 하나의 메가 프롬프트/단일 스킬 | 아니오 | 아니오(자체 확인) | 약함(채팅 메모리) | 약함—진행 상황이 세션과 함께 사라짐 |
| **longgraph(이 리포지토리)** | **아니오—Markdown만** | **예(슈퍼바이저 노드)** | **예(`ledger.md`)** | **예—파일이 실행; 프롬프트를 재전송** |

관련 검색: *longgraph 스킬*, *장기 수평선 에이전트 스킬*, *장기 실행 에이전트 스킬*, *에이전트 드리프트 방지*, *멀티태스크 에이전트 루프*, *작업 중 AI 코딩 호스트 전환*, *Claude Code 멀티 에이전트 슈퍼바이저*, *Grok Build 에이전트 루프*, *에이전트 원장*, *루프 그래프*, *에이전트를 위한 그래프 엔지니어링*, *클린 컨텍스트 리뷰*.

## 왜 longgraph인가?

장기 실행 에이전트는 예측 가능한 방식으로 드리프트하는 경향이 있습니다: 범위가 확장되고, "완료"가 자체 보고되고, 테스트가 실제 경로를 증명하지 않으며, 초기 결정이 컨텍스트에서 사라집니다. longgraph는 보호 장치를 모델의 메모리 외부로 이동합니다:

- **작성만 된 것이 아니라 검증됨**—수용 게이트가 실제 출력에 대해 재실행됩니다.
- **지속적인 상태**—원장은 컨텍스트 손실을 견디고 단일 스코어보드로 남아 있습니다.
- **많은 장기 작업, 하나의 루프**—원장은 지속적인 큐; 항목은 독립적일 수 있습니다(마이그레이션, 테스트 부채, 문서, 게이트) 하나의 메가 목표를 강제하지 않고.
- **호스트 이식 가능**—진행 상황은 `.longgraph/<date-slug>/` 아래의 파일이며, 채팅 기록이 아닙니다. 다른 호스트를 동일한 워크스페이스로 가리키고, 컴파일된 노드 프롬프트를 재전송하고, 다음 열린 원장 항목을 가져옵니다.
- **클린 컨텍스트 리뷰**—독립적인 슈퍼바이저가 실행자가 볼 수 없는 드리프트를 잡을 수 있습니다.
- **강제 수렴**—성장이 주기적으로 중지되고, 측정되고, 단순화됩니다.
- **낮은 마찰의 소유자 결정**—진정한 소유자 전용 호출은 짧은 권장 A/B/C 선택으로 도착하며, 기술적인 숙제 과제가 아닙니다.

이것은 Markdown이며, 오케스트레이션 프레임워크가 아닙니다: 애플리케이션 런타임, 서버 또는 벤더 락인이 없습니다. **Claude Code 플러그인**으로 설치하거나, **Codex / Cursor / Grok Build**에 심볼릭 링크를 생성하세요(설치 스크립트 참조). Grok Build의 런타임 노드는 **프롬프트만** 유지—두 개의 `/loop` 붙여넣기, 직접 실행 없음.

## 멀티태스크 루프 및 호스트 전환

**하나의 루프는 큐이며, 단일 스토리가 아닙니다.** 각 라운드는 여전히 하나의 독립적으로 검증 가능한 원장 작업 항목을 엔드투엔드로 완료합니다(구현→검증→기록). 그 항목은 동작 주장, 쓰기 세트 및 게이트를 공유하는 결합된 변경의 하나의 일관된 워크셋일 수 있습니다; 관련 없는 작업은 별도로 유지됩니다. 원장은 한 번에 많은 긴 항목을 보유할 수 있습니다—관련된 마일스톤 *또는* 관련 없는 백로그(게이트 대기 백로그 패턴은 극단적인 경우: 감사 중인 항목에 의존하지 않는 유용한 작업). 다음 긴 작업이 다른 것에 대한 것일 때마다 새 그래프가 필요하지 않습니다.

**호스트는 교환 가능; 파일은 교환 불가능합니다.** 컴파일된 루프 그래프 실행은 프롬프트와 상태를 `.longgraph/<date-slug>/` 아래에 동결합니다. 다른 곳에서 계속하려면:

1. 해당 파일(및 프로젝트)을 볼 수 있는 워크스페이스를 사용하세요.
2. 새 호스트에서 동일한 동결된 executor(및, 사용된 경우, supervisor) 프롬프트를 재전송하세요.
3. 노드는 `ledger.md` / `directives.md`를 읽고 다음 열린 항목에서 계속합니다.

채팅 대화 내용을 내보내는 것이 아닙니다. 호출 구문은 여전히 각 호스트의 방언을 따릅니다([호스트별 참조](skills/loop-graph/references/))—*진행 상황*만 이식 가능합니다.

## longgraph가 올바른 도구인가요?

| 작업 형태 | 선택 | 얻는 것 |
| --- | --- | --- |
| 일반 작업/세션에 맞는 하나의 자체 완결형 목표 | 호스트의 일반 작업 또는 목표를 직접 사용 | longgraph 래퍼 또는 추가 프롬프트 레이어 없음 |
| 많은 검증된 슬라이스에 걸친 기능, 통합, 마이그레이션 또는 동작 요구 사항 | [**`/loop-deliver`**](skills/loop-deliver/README.md) | 공유 그래프에 대한 요구 사항 팩, 추적 가능한 수용 증명 포함 |
| 여러 라운드의 미사용/중복/재사용/슬림화(동일한 2노드 그래프) | [**`/loop-converge`**](skills/loop-converge/README.md) | 사전 바인딩된 수렴 팩이 있는 공유 컴파일러 |
| 오픈 소스 증거, 주요 연구 및 실험으로 실행 가능한 접근 방식 비교 | [**`/loop-research`**](skills/loop-research/README.md) | 증거 주도 결정 팩; 결과를 비교할 수 있는 경우에만 선택 |
| 위에서 다루지 않은 커스텀 형태를 가진 많은 라운드 | [**longgraph / loop-graph**](skills/loop-graph/README.md) | 커스텀 그래프 실행을 위한 공유 컴파일러 |

**경험 법칙:** 그래프가 필요하지 않다면 longgraph를 사용하지 마세요.

## 빠른 시작

### Claude Code

마켓플레이스에서 플러그인 설치:

```text
/plugin marketplace add levi-qiao/longgraph-skill
/plugin install longgraph@longgraph-skill
```

### Codex, Cursor 또는 Grok Build

라이브러리를 설치하고, 심볼릭 링크를 따르는 호스트에 `/longgraph`, `/loop-converge`, `/loop-deliver`, `/loop-research`를 배치하세요:

```sh
curl -fsSL https://raw.githubusercontent.com/levi-qiao/longgraph-skill/main/install.sh | sh
```

로컬 클론에서, 리포지토리 루트에서 `./install.sh`를 실행하세요.

Grok Build에서의 저작은 해당 설치 후 `/longgraph`입니다. 두 런타임 노드를 시작하는 것은 여전히 프롬프트만: 컴파일된 `/loop` 라인을 붙여넣으세요—[Grok Build](skills/loop-graph/references/grok.md)를 참조하세요. Cursor 및 shell/cron은 동일한 프롬프트 전용 실행 경로를 사용합니다—[호스트 호환성](#호스트-호환성)을 참조하세요.

### 실행 설계

`/longgraph`를 호출하세요; 정리를 `/loop-converge`로, 요구 사항을 `/loop-deliver`로, 증거 주도 옵션 선택을 `/loop-research`로 라우팅합니다. 현재 호스트를 감지하고, 워크스페이스를 검사하며, 실행을 컴파일하기 전에 해결되지 않은 소유자 결정만 묻습니다. Codex 또는 Claude Code에서 직접 생성을 선택하여 동일한 호스트 런타임 노드 두 개를 시작하거나, 수동/크로스 호스트 실행용 프롬프트만 선택하세요(Grok Build 포함). 진정으로 커스텀 실행 형태의 경우에만 `loop-graph`를 직접 사용하세요.

저작과 런타임은 별도로 유지됩니다: 저자 스킬은 작업을 컴파일하지만 결코 실행하지 않습니다. 생성된 노드는 `.longgraph/<date-slug>/` 아래의 동결된 실행 계약을 따릅니다.

## 그래프 작동 방식

| 역할 | 책임 | 지속적인 엣지 |
| --- | --- | --- |
| **Executor** | 하나의 독립적으로 검증 가능한 원장 작업 항목을 처리하고, 동일한 라운드에서 검증하고, 결과를 기록 | `ledger.md`를 읽고 쓰기 |
| **Supervisor** | 자체 별도 컨텍스트에서 재검증하고, 통과한 작업을 체크포인트하고, 드리프트를 수정 | 원장을 읽음; 지시사항 엣지(라이브 큐+콜드 아카이브)를 통해서만 조종 |
| **Scout** *(선택사항)* | 중요 경로에서 벗어나 제한된 질문을 조사 | 참조 시에만 읽히는 조사 결과 파일을 작성 |

부하 지지 규칙은 **하나의 노드=하나의 프롬프트+하나의 단일 작성자 엣지**입니다. 원장에는 정확히 한 명의 작성자가 있습니다. 슈퍼바이저는 실행자의 컨텍스트를 결코 공유하지 않으며, 스코어보드를 편집하지 않으며, 단방향 지시사항 엣지를 통해서만 조종합니다.

모든 제약 조건의 근거는 [방법론](lib/methodology.md)을 읽으세요. 노드 및 엣지 모델은 [loop-graph 모델](skills/loop-graph/docs/model.md)을 참조하세요.

## 호스트 호환성

| 호스트 | loop-graph 실행 |
| --- | --- |
| [**Codex**](skills/loop-graph/references/codex.md) | ✅ 호스트를 감지하고 두 런타임 노드를 직접 생성 |
| [**Claude Code**](skills/loop-graph/references/claude-code.md) | ✅ 호스트를 감지하고 기능 검사가 통과되면 두 백그라운드 런타임 세션을 직접 생성 |
| [**Grok Build**](skills/loop-graph/references/grok.md) | 프롬프트만—두 개의 `/loop` 작업(executor + supervisor), 웨이크 엣지 없음 |
| [**Cursor**](skills/loop-graph/references/cursor.md) | 프롬프트 전용 실행 대상 |
| [**shell / cron**](skills/loop-graph/references/shell-cron.md) | 프롬프트 전용 실행 대상 |

권위 있는 구문, 페이싱, 컨텍스트 캐리 및 후크는 별도의 [호스트별 참조](skills/loop-graph/references/)에 있으므로, 저작은 선택된 호스트만 로드합니다. 실행 중 호스트 전환은 동일한 지속적인 실행 디렉토리를 재사용합니다; 각 틱을 시작하는 방법만 변경됩니다.

## 리포지토리 맵

| 경로 | 목적 |
| --- | --- |
| [루트 `SKILL.md`](SKILL.md) | `/longgraph` 라우터; 집중 팩 또는 커스텀 컴파일러 경로 선택 |
| [Loop-graph 컴파일러](skills/loop-graph/SKILL.md) | 공유 executor, supervisor, ledger, directive 및 ops 아티팩트 생성 |
| [loop-converge](skills/loop-converge/SKILL.md) | 프리셋 진입점: 코드 수렴 인터뷰→동일한 loop-graph 컴파일 |
| [loop-deliver](skills/loop-deliver/SKILL.md) | 프리셋 진입점: 요구 사항 전달 인터뷰→동일한 컴파일 |
| [loop-research](skills/loop-research/SKILL.md) | 프리셋 진입점: 증거 주도 솔루션 선택 인터뷰→동일한 컴파일 |
| [프리셋 계약](skills/loop-graph/docs/preset-contract.md) | 공유 컴파일러와 목표별 팩 간의 경계 |
| [`lib/`](lib) | 공유 방법론 |
| [호스트 참조](skills/loop-graph/references) | 각 호스트의 런타임 사실을 위한 하나의 독립적으로 로드된 소유자 |
| [실제 예제](skills/loop-graph/examples) | 공개 Git 자체 반복+작동 중인 게이트를 보여주는 가상 원장 |
| [공개/개인 경계](docs/public-private-boundary.md) | 공개 트리에 들어갈 수 있는 것과 프로젝트 로컬로 남아 있는 것 |

## 거버넌스

longgraph는 자체 안티 블로트 규칙을 라이브러리에 적용합니다: **그 가치를 증명한 실제 실행 없이는 프롬프트가 들어가지 않습니다.** 큐레이션되고 의견이 있는 것이 포괄적인 것을 이깁니다.

기여는 환영합니다. [기여 가이드](CONTRIBUTING.md)로 시작하세요.

## 🔒 보안 및 개인정보

이 포크에는 추가 보안 도구가 포함되어 있습니다:

```bash
# 커밋 전에 .longgraph 디렉토리 스캔
./scripts/scrub-longgraph-secrets.sh

# 특정 실행 스캔
./scripts/scrub-longgraph-secrets.sh .longgraph/2026-09-08-auth-migration

# 드라이런으로 스캔 내용 확인
./scripts/scrub-longgraph-secrets.sh --dry-run
```

자세한 내용은 [FORK.md](FORK.md)를 참조하세요.

## 📊 관찰 가능성

실행 상태를 추적하려면:

```bash
# 모든 실행의 상태 확인
find .longgraph -name status.json -exec jq . {} \;
```

스키마 및 통합 세부 정보는 [docs/observability/status-schema.md](docs/observability/status-schema.md)를 참조하세요.

## 크레딧

loop-graph 스킬은 실제 실행과 커뮤니티 입력에서 성장했습니다. [공개 Git 자체 반복 사례](skills/loop-graph/examples/self-iteration-longgraph-skill/README.md)는 메소드가 이 라이브러리로 강화된 방법을 기록합니다. 특별히 감사드립니다 [@BrightProgrammer7](https://github.com/BrightProgrammer7)에게, `migrate-blob-storage` 예제와 마일스톤 게이트 및 노드/엣지 어휘를 날카롭게 한 토론에 대해.

이 포크의 개선 사항은 [Samek86](https://github.com/Samek86)이 유지 관리합니다.

## 라이선스

[MIT](LICENSE) © 2026 [levi-qiao](https://github.com/levi-qiao)

포크 개선 사항 © 2026 [Samek86](https://github.com/Samek86)
