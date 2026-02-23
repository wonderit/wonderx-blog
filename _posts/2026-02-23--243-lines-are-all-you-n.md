---
title: '243줄로 GPT를 구현한다고? Karpathy의 미니멀리즘이 말하는 것'
description: 'Andrej Karpathy가 Python 243줄로 전체 GPT를 구현했다. 복잡한 AI 프레임워크 없이. 이 코드 한 줄씩 읽다 보면 "나 GPT 제대로 알고 있던 건 맞나?"라는 질문이 자연스럽게 나온다.'
date: 2026-02-23 09:25:44 +0900
image: /images/blog/-243-lines-are-all-you-n-1.webp
tags: ['AI', 'GPT', 'Karpathy', '딥러닝', 'Python', 'transformer']
categories: [tech]
author: wonder
twin: -243-lines-are-all-you-n-en
---

GPT-4o를 파인튜닝하고, RAG 파이프라인 깔고, LangChain으로 에이전트 만들고 있는데 — **GPT가 실제로 어떻게 돌아가는지 설명할 수 있나?**

Attention is all you need 논문 읽었다고 해서 이해한 건 아니다. 수식만 봤지 실제 코드로 구현한 사람이 얼마나 될까. Andrej Karpathy는 그냥 보여줬다. 243줄로.

---

## Karpathy가 또 해냈다

Andrej Karpathy — OpenAI 공동 창업자, Tesla AI 총괄을 거친 이 사람은 항상 "핵심만 남기는" 작업을 즐긴다. 그의 GitHub에는 `micrograd`, `nanoGPT`, `llm.c` 같은 미니멀 구현체들이 즐비하다. 이번엔 Python 243줄짜리 GPT다.

그냥 토이 프로젝트가 아니다. **실제 작동하는 트랜스포머 언어 모델**이다. 의존성이라곤 NumPy 하나뿐.

![](/images/blog/-243-lines-are-all-you-n-2.webp)

---

## 243줄 안에 뭐가 들어가 있나

놀라운 건 이게 진짜 "완전한" GPT라는 거다. 핵심 컴포넌트를 하나씩 뜯어보면:

### 1. Tokenizer (토크나이저)
문자를 정수 인덱스로 변환하는 character-level tokenizer. 단어 단위 BPE는 아니지만 원리는 동일하다. 어휘집(vocab)을 구성하고 인코딩/디코딩 함수를 구현하는 데 10줄도 안 걸린다.

### 2. Embedding Layer (임베딩)
Token embedding + Positional embedding. `n_embd` 차원의 벡터 공간에 각 토큰을 매핑한다. 위치 정보를 학습 가능한 행렬로 더해주는 방식.

```python
# 핵심은 이게 전부다
tok_emb = self.token_embedding_table(idx)   # (B, T, C)
pos_emb = self.position_embedding_table(pos)  # (T, C)
x = tok_emb + pos_emb
```

### 3. Multi-Head Self-Attention (핵심 중 핵심)
Q, K, V 행렬 연산. 마스킹으로 미래 토큰 차단. 수식으로 보면 무서운데 코드로 보면 행렬 곱셈 몇 번이 전부다.

```python
att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
att = att.masked_fill(self.bias[:,:,:T,:T] == 0, float('-inf'))
att = F.softmax(att, dim=-1)
```

### 4. Feed-Forward Network
Attention 후에 오는 2층 MLP. ReLU 대신 GELU 활성화 함수 사용. 여기서 "기억"을 저장하는 역할을 한다는 연구도 있다.

### 5. Training Loop
Cross-entropy loss, AdamW optimizer, learning rate scheduling까지. 243줄 안에 다 들어간다.

![](/images/blog/-243-lines-are-all-you-n-3.webp)

---

## 왜 이게 중요한가 — 데이터로 말하자

| 항목 | PyTorch + HuggingFace | Karpathy 243줄 |
|------|----------------------|----------------|
| 의존성 | 수십 개 | NumPy 1개 |
| 코드 줄 수 | 수천 줄 | 243줄 |
| 이해 가능성 | 낮음 | 높음 |
| 성능 | 최고 | 학습용 |
| 개념 전달력 | 낮음 | **최고** |

프레임워크는 최적화와 편의를 위한 래퍼(wrapper)다. 그 안에서 무슨 일이 벌어지는지는 결국 수학과 코드다.

---

## 브로드 연구소에서의 기억

이 코드를 보다가 오래된 기억이 올라왔다.

**Broad Institute of MIT and Harvard**에서 visiting PhD student로 연구하던 시절. 그때 내가 맡은 건 multi-party computation(다자간 연산)을 PyTorch의 **한 줄을 C로 구현**하는 작업이었다.

암호화된 상태에서 딥러닝 연산을 수행해야 했기 때문에, 프레임워크 추상화 뒤에 숨을 수가 없었다. **weight initialization**부터 다시 시작했다. Xavier init, He init을 수식 그대로 C로 쐈다. **activation function**은 선형 근사로 쪼개야 했다. GELU를 다항식으로 근사하고, 그 오차가 실제 학습에 어떤 영향을 미치는지 하나하나 추적했다.

![](/images/blog/-243-lines-are-all-you-n-4.webp)

**backpropagation**은 압권이었다. math 라이브러리, Eigen(행렬 연산), Boost(유틸리티)를 엮어가며 그래디언트를 손으로 유도하고 코드로 옮겼다. 네트워크 레이어 간 통신 비용까지 고려해가며 C로 컴파일, 빌드, 디버깅을 반복했다.

몇 주가 걸렸다. 하지만 그 과정에서 얻은 건 — 딥러닝이 "어떻게" 돌아가는지에 대한 완전한 직관이었다.

---

## 지금 AI 개발자들에게 묻고 싶은 것

요즘 AI 개발자 중에 **scratch에서 MLP 트레이닝을 직접 해본 사람이 얼마나 될까?**

파인튜닝? 많다. RAG? 넘친다. LLM API 콜? 당연히 많다. 그런데 역전파를 직접 구현해서, 그래디언트가 어떻게 흐르는지 눈으로 확인한 사람?

네트워크 레이턴시까지 고려하면서 C로 컴파일하고 빌드하고 디버깅까지 해본 사람은?

이건 단순한 "옛날 방식 타령"이 아니다. **AI 툴이 발전할수록 원리를 아는 사람과 모르는 사람의 격차는 더 벌어진다.**

![](/images/blog/-243-lines-are-all-you-n-5.webp)

예를 들어 attention head 수를 늘리면 왜 성능이 올라가다 갑자기 떨어지는지, learning rate warm-up이 왜 필요한지, weight decay가 어떻게 과적합을 막는지 — 이걸 직관으로 이해하는 사람은 하이퍼파라미터 튜닝을 다르게 접근한다. "해봤더니 좋았다"가 아니라 "이 이유로 이 방향이 맞다"로 간다.

---

## 243줄이 보여주는 것

Karpathy가 243줄로 보여준 건 단순히 "이렇게 짧게도 된다"가 아니다.

**GPT의 본질적인 복잡도는 생각보다 낮다는 것.**

트랜스포머의 혁신은 사실 몇 가지 아이디어의 조합이다:
1. Self-attention: 시퀀스 내 임의 위치 간 직접 연결
2. Residual connection: 그래디언트 흐름 보장
3. Layer normalization: 학습 안정화
4. 대규모 데이터 + 파라미터 스케일링

이 네 가지를 제대로 이해하면 GPT-2든 GPT-4든 구조적 차이는 "더 크고 더 많이" 수준이다.

![](/images/blog/-243-lines-are-all-you-n-6.webp)

---

## 그래서 이걸 읽어야 하나?

**읽어야 한다.** 조건 없이.

AI를 도구로만 쓰는 사람에게도, AI 연구자를 목표로 하는 사람에게도. LLM 프레임워크 위에서 일하는 엔지니어에게도.

Karpathy의 243줄은 교과서보다 낫다. 수식이 코드가 되고, 코드가 결과가 되는 과정을 한 파일 안에서 전부 볼 수 있다.

나는 이번 주말에 이 코드를 처음부터 끝까지 다시 읽어볼 생각이다. 브로드 연구소 시절 C로 구현했던 기억을 떠올리면서.

그때는 "왜 이 고생을 하나" 싶었다. 지금은 그게 있어서 다행이라고 생각한다.

![](/images/blog/-243-lines-are-all-you-n-7.webp)

---

## 마무리

AI 툴은 계속 좋아진다. Copilot이 코드를 쓰고, Claude가 설계를 도와주고, Cursor가 리팩토링을 제안한다. 좋은 일이다.

그런데 그 도구들이 뭘 하는지 모르는 사람이 그걸 쓰면, 결국 "잘 돌아가는 것 같은데 왜 이상한 결과가 나오지?"에서 멈춘다.

**243줄은 그 물음표를 없애주는 코드다.**

읽어봐라. 진짜로.

---

*참고: Andrej Karpathy의 코드는 GitHub에서 찾을 수 있다. [Towards Deep Learning 원문](https://www.towardsdeeplearning.com/andrej-karpathy-just-built-an-entire-gpt-in-243-lines-of-python-7d66cfdfa301)*
