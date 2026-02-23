---
title: "198줄로 GPT를 구현한다고? Karpathy의 미니멀리즘이 말하는 것"
description: "Andrej Karpathy가 Python 198줄로 전체 GPT를 구현했다. PyTorch도 NumPy도 없이. 이 코드 한 줄씩 읽다 보면 \"나 GPT 제대로 알고 있던 건 맞나?\"라는 질문이 자연스럽게 나온다."
date: 2026-02-20 09:00:00 +0900
image: /images/blog/-198-lines-are-all-you-n-1.webp
tags: ['AI', 'GPT', 'Karpathy', '딥러닝', 'Python', 'transformer']
categories: [tech]
author: wonder
lang: ko
twin: 198-lines-are-all-you-need-en
---

GPT-4o를 파인튜닝하고, RAG 파이프라인 깔고, LangChain으로 에이전트 만들고 있는데 — **GPT가 실제로 어떻게 돌아가는지 설명할 수 있나?**

Attention is all you need 논문 읽었다고 해서 이해한 건 아니다. 수식만 봤지 실제 코드로 구현한 사람이 얼마나 될까. Andrej Karpathy는 그냥 보여줬다. 198줄로.

---

## Karpathy가 또 해냈다

2026년 2월 11일, Andrej Karpathy가 Python 파일 하나를 올렸다. 198줄. **의존성 제로.** PyTorch도 없고, TensorFlow도 없고, NumPy조차 없다. `os`, `math`, `random`, `argparse` — 표준 라이브러리만으로 GPT를 처음부터 끝까지 구현했다.

Karpathy 본인은 이걸 "아트 프로젝트"라고 불렀다. 하지만 실상은 **지금 존재하는 가장 좋은 AI 교육 자료**다.

![](/images/blog/-198-lines-are-all-you-n-2.webp)

---

## 198줄 안에 뭐가 들어가 있나

microGPT가 하는 일은 단순하다. 아기 이름 데이터를 다운로드하고, 패턴을 학습한 다음, 실제로 존재하지 않지만 그럴듯한 이름을 생성한다. ChatGPT와 동일한 알고리즘이다. Attention, 학습 루프, 다음 토큰 예측 — 수학이 같다. 스케일만 다를 뿐.

### 1. Tokenizer — 문자를 숫자로

```python
chars = ['<BOS>', '<EOS>'] + sorted(list(set(''.join(docs))))
stoi = { ch:i for i, ch in enumerate(chars) }
itos = { i:ch for i, ch in enumerate(chars) }
```

`<BOS>`(시작)와 `<EOS>`(종료) 특수 토큰 포함해서 character-level tokenizer를 구현한다. ChatGPT의 BPE와 원리는 동일하다.

### 2. Autograd Engine — 핵심 중 핵심

이 코드의 진짜 아름다움은 여기에 있다. Karpathy가 약 40줄로 **PyTorch의 autograd 엔진을 처음부터 구현**했다.

```python
class Value:
    def __init__(self, data, _children=(), _op=''):
        self.data = data
        self.grad = 0
        self._backward = lambda: None
        self._prev = set(_children)
```

`Value` 클래스는 네트워크의 모든 숫자를 감싸고, 연산 그래프를 자동으로 추적한다. 덧셈하면 gradient가 그대로 전파되고, 곱셈하면 "스왑 규칙"이 적용된다 — `c = a * b`일 때 a의 gradient는 `b × ∂c`, b의 gradient는 `a × ∂c`. 이게 미적분의 chain rule이다. 4줄로 구현된.

역전파는 topological sort로 올바른 순서를 보장한다. PyTorch에서 `loss.backward()` 호출할 때 내부에서 돌아가는 바로 그 알고리즘을 Python 리스트와 재귀로 구현한 거다.

### 3. Model Parameters — 뇌의 구조

```python
state_dict = {'wte': matrix(vocab_size, n_embd),
              'wpe': matrix(block_size, n_embd)}
```

- **wte** (Word Token Embedding): 각 토큰을 16차원 벡터로 변환
- **wpe** (Word Position Embedding): 시퀀스 내 위치 정보 인코딩
- 각 트랜스포머 레이어: **attn_wq/wk/wv** (Q, K, V 행렬), **mlp_fc1/fc2** (Feed-Forward)

기본 설정: 16차원 임베딩, 4개 어텐션 헤드, 1레이어, 시퀀스 길이 8. 총 약 **4,000개 파라미터.** GPT-4는 1조 개가 넘는다. 같은 구조, 다른 스케일.

### 4. GPT Architecture — Attention이 벌어지는 곳

Embedding → **RMSNorm** → Multi-Head Self-Attention → Residual Connection → MLP → 반복.

**RMSNorm**: LayerNorm의 간소화 버전. 값이 폭발하거나 소멸하지 않도록 정규화한다.

**Self-Attention**: 현재 토큰의 Query가 이전 토큰들의 Key와 dot product로 호환성 점수를 계산하고, softmax로 확률화한 후, Value 벡터를 가중 합산한다. 4개 헤드가 각각 다른 관점(모음 패턴, 최근 문자 등)을 학습한다.

**Squared ReLU**: 일반 ReLU 대신 제곱 ReLU를 사용한다. 음수는 0, 양수는 제곱 — 더 강한 비선형성을 준다. GELU 대신 이걸 쓴 건 Karpathy의 단순화 전략.

**Weight Tying**: 임베딩 행렬(`wte`)을 출력 projection에도 재사용한다. 토큰→벡터 변환에 쓴 행렬을 벡터→토큰 예측에도 쓰는 것.

### 5. Training Loop — Adam Optimizer까지

```python
loss = -probs[tokens[pos_id + 1]].log()
```

모델이 다음 문자를 예측하고, 정답과의 negative log likelihood를 계산한다. 그리고 `loss.backward()`로 모든 파라미터의 gradient를 구한 뒤, **Adam optimizer**가 업데이트한다. Adam은 gradient의 이동 평균(momentum)과 크기 평균을 추적해서 더 안정적으로 학습시킨다. GPT-4, DALL-E 훈련에 쓰이는 바로 그 optimizer다.

### 6. Inference — 이름 생성

BOS 토큰으로 시작, 모델이 확률 분포에서 다음 토큰을 샘플링, 그걸 다시 입력으로 넣고, EOS가 나올 때까지 반복. **이것이 autoregressive generation** — ChatGPT가 메시지 보낼 때마다 하는 바로 그 과정이다.

![](/images/blog/-198-lines-are-all-you-n-3.webp)

---

## 왜 이게 중요한가 — 데이터로 말하자

| 항목 | PyTorch + HuggingFace | Karpathy 198줄 |
|------|----------------------|----------------|
| 의존성 | 수십 개 | **제로** (순수 Python) |
| 코드 줄 수 | 수천 줄 | 198줄 |
| 이해 가능성 | 낮음 | 높음 |
| 성능 | 최고 | 학습용 |
| 개념 전달력 | 낮음 | **최고** |

Karpathy 본인의 말: *"This is the full algorithmic content of what is needed. Everything else is just for efficiency."*

프레임워크는 최적화와 편의를 위한 래퍼(wrapper)다. 그 안에서 무슨 일이 벌어지는지는 결국 수학과 코드다.

---

## 브로드 연구소에서의 기억

이 코드를 보다가 오래된 기억이 올라왔다.

**Broad Institute of MIT and Harvard**에서 visiting PhD student로 연구하던 시절. 그때 내가 맡은 건 multi-party computation(다자간 연산)을 PyTorch의 **한 줄을 C로 구현**하는 작업이었다.

암호화된 상태에서 딥러닝 연산을 수행해야 했기 때문에, 프레임워크 추상화 뒤에 숨을 수가 없었다. **weight initialization**부터 다시 시작했다. Xavier init, He init을 수식 그대로 C로 쐈다. **activation function**은 선형 근사로 쪼개야 했다. GELU를 다항식으로 근사하고, 그 오차가 실제 학습에 어떤 영향을 미치는지 하나하나 추적했다.

![](/images/blog/-198-lines-are-all-you-n-4.webp)

**backpropagation**은 압권이었다. math 라이브러리, Eigen(행렬 연산), Boost(유틸리티)를 엮어가며 그래디언트를 손으로 유도하고 코드로 옮겼다. 네트워크 레이어 간 통신 비용까지 고려해가며 C로 컴파일, 빌드, 디버깅을 반복했다.

몇 주가 걸렸다. 하지만 그 과정에서 얻은 건 — 딥러닝이 "어떻게" 돌아가는지에 대한 완전한 직관이었다.

---

## 지금 AI 개발자들에게 묻고 싶은 것

요즘 AI 개발자 중에 **scratch에서 MLP 트레이닝을 직접 해본 사람이 얼마나 될까?**

파인튜닝? 많다. RAG? 넘친다. LLM API 콜? 당연히 많다. 그런데 역전파를 직접 구현해서, 그래디언트가 어떻게 흐르는지 눈으로 확인한 사람?

네트워크 레이턴시까지 고려하면서 C로 컴파일하고 빌드하고 디버깅까지 해본 사람은?

이건 단순한 "옛날 방식 타령"이 아니다. **AI 툴이 발전할수록 원리를 아는 사람과 모르는 사람의 격차는 더 벌어진다.**

![](/images/blog/-198-lines-are-all-you-n-5.webp)

예를 들어 attention head 수를 늘리면 왜 성능이 올라가다 갑자기 떨어지는지, learning rate warm-up이 왜 필요한지, weight decay가 어떻게 과적합을 막는지 — 이걸 직관으로 이해하는 사람은 하이퍼파라미터 튜닝을 다르게 접근한다. "해봤더니 좋았다"가 아니라 "이 이유로 이 방향이 맞다"로 간다.

---

## 198줄이 보여주는 것 — Karpathy의 6년 압축 여정

이건 갑자기 나온 게 아니다. Karpathy는 6년에 걸쳐 추상화를 하나씩 벗겨냈다:

- **2020**: `micrograd` (autograd 엔진)
- **2020**: `minGPT` (PyTorch GPT)
- **2023**: `nanoGPT` (프로덕션급 훈련)
- **2024**: `llm.c` (순수 C/CUDA, 프레임워크 없음)
- **2026**: `microGPT` (**알고리즘 그 자체, 그 외 아무것도 없음**)

매 단계마다 한 겹씩 벗겼다. 이 마지막 버전은 전부 벗겼다.

**GPT의 본질적인 복잡도는 생각보다 낮다는 것.**

트랜스포머의 혁신은 사실 몇 가지 아이디어의 조합이다:
1. Self-attention: 시퀀스 내 임의 위치 간 직접 연결
2. Residual connection: 그래디언트 흐름 보장
3. Layer normalization: 학습 안정화
4. 대규모 데이터 + 파라미터 스케일링

이 네 가지를 제대로 이해하면 GPT-2든 GPT-4든 구조적 차이는 "더 크고 더 많이" 수준이다. 올해 AI 인프라에 4,000억 달러가 투입된다. 그런데 그 전부를 움직이는 핵심 알고리즘? README보다 짧은 파일 하나에 들어간다.

![](/images/blog/-198-lines-are-all-you-n-6.webp)

---

## 그래서 이걸 읽어야 하나?

**읽어야 한다.** 조건 없이.

AI를 도구로만 쓰는 사람에게도, AI 연구자를 목표로 하는 사람에게도. LLM 프레임워크 위에서 일하는 엔지니어에게도.

Karpathy의 198줄은 교과서보다 낫다. 수식이 코드가 되고, 코드가 결과가 되는 과정을 한 파일 안에서 전부 볼 수 있다.

나는 이번 주말에 이 코드를 처음부터 끝까지 다시 읽어볼 생각이다. 브로드 연구소 시절 C로 구현했던 기억을 떠올리면서.

그때는 "왜 이 고생을 하나" 싶었다. 지금은 그게 있어서 다행이라고 생각한다.

![](/images/blog/-198-lines-are-all-you-n-7.webp)

---

## 마무리

AI 툴은 계속 좋아진다. Copilot이 코드를 쓰고, Claude가 설계를 도와주고, Cursor가 리팩토링을 제안한다. 좋은 일이다.

그런데 그 도구들이 뭘 하는지 모르는 사람이 그걸 쓰면, 결국 "잘 돌아가는 것 같은데 왜 이상한 결과가 나오지?"에서 멈춘다.

**198줄은 그 물음표를 없애주는 코드다.**

읽어봐라. 진짜로.

---

**참고 자료:**
- [Andrej Karpathy의 microGPT — GitHub Gist](https://gist.github.com/karpathy/8627fe009c40f57531cb18360106ce95)
- [Sumit Pandey의 코드 해설 원문 — Towards Deep Learning](https://www.towardsdeeplearning.com/andrej-karpathy-just-built-an-entire-gpt-in-243-lines-of-python-7d66cfdfa301)
