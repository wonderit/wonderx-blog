---
title: "198 Lines Are All You Need: What Karpathy's Minimalism Is Really Telling Us"
description: "Andrej Karpathy built a fully working GPT in 198 lines of pure Python — no PyTorch, no NumPy, zero dependencies. Reading through it line by line forces a question: did I actually understand GPT all along?"
date: 2026-02-20 09:00:00 +0900
image: /images/blog/-198-lines-are-all-you-n-1.webp
tags: ['AI', 'GPT', 'Karpathy', 'deep learning', 'Python', 'transformer']
categories: [tech]
author: wonder
lang: en
twin: 198-lines-are-all-you-need
---

You're fine-tuning GPT-4o, wiring up RAG pipelines, building agents with LangChain — but can you actually explain **how a GPT works under the hood?**

Reading the "Attention Is All You Need" paper doesn't count. Recognizing the equations isn't the same as understanding them. Andrej Karpathy just proved the point — by building the whole thing in 198 lines.

---

## Karpathy Did It Again

On February 11, 2026, Andrej Karpathy dropped a single Python file. 198 lines. **Zero dependencies.** No PyTorch, no TensorFlow, not even NumPy. Just `os`, `math`, `random`, and `argparse` — standard library only.

He called it an "art project." But it's really **the best AI education that exists on the internet right now.**

![](/images/blog/-198-lines-are-all-you-n-2.webp)

---

## What Fits in 198 Lines

microGPT downloads a list of baby names, learns the patterns, then generates new names that sound real but never existed. Same concept as ChatGPT — same attention mechanism, same training loop, same next-token prediction math. Just at micro scale.

### 1. Tokenizer — Characters to Numbers

```python
chars = ['<BOS>', '<EOS>'] + sorted(list(set(''.join(docs))))
stoi = { ch:i for i, ch in enumerate(chars) }
itos = { i:ch for i, ch in enumerate(chars) }
```

Character-level tokenizer with `<BOS>` (beginning) and `<EOS>` (end) special tokens. Same principle as ChatGPT's BPE tokenizer.

### 2. The Autograd Engine — The Heart of Everything

This is where the code gets beautiful. Karpathy builds a mini PyTorch autograd engine in about 40 lines.

```python
class Value:
    def __init__(self, data, _children=(), _op=''):
        self.data = data
        self.grad = 0
        self._backward = lambda: None
        self._prev = set(_children)
```

The `Value` class wraps every number in the network and silently builds an operation graph. Addition propagates gradients directly. Multiplication uses the "swap rule" — if `c = a * b`, then a's gradient is `b × ∂c` and b's gradient is `a × ∂c`. That's the chain rule from calculus, implemented in 4 lines.

Backward pass uses topological sort to ensure correct gradient order. This is literally the same algorithm inside PyTorch's `loss.backward()` — written from scratch with Python lists and recursion.

### 3. Model Parameters — The Brain

- **wte** (Word Token Embedding): converts each token into a 16-dimensional vector
- **wpe** (Word Position Embedding): encodes position in the sequence
- Per transformer layer: **attn_wq/wk/wv** (Q, K, V matrices), **mlp_fc1/fc2** (feed-forward)

Default config: 16 embedding dims, 4 attention heads, 1 layer, sequence length 8. Roughly **4,000 parameters.** GPT-4 has over a trillion. Same architecture, wildly different scale.

### 4. GPT Architecture — Where Magic Happens

Embedding → **RMSNorm** → Multi-Head Self-Attention → Residual Connection → MLP → repeat.

**RMSNorm**: a simpler cousin of LayerNorm. Keeps values from exploding or vanishing.

**Self-Attention**: current token's Query computes dot products with all previous tokens' Keys, softmax turns them into probabilities, then Value vectors get mixed accordingly. 4 heads run in parallel, each learning different patterns.

**Squared ReLU**: instead of GELU, Karpathy uses ReLU squared — negatives become 0, positives get squared for stronger non-linearity. A deliberate simplification.

**Weight Tying**: the same embedding matrix (`wte`) is reused for output projection. The weights that convert tokens to embeddings also convert embeddings back to predictions.

### 5. Training Loop — With Full Adam Optimizer

```python
loss = -probs[tokens[pos_id + 1]].log()
```

The model predicts the next character, computes negative log likelihood against the truth, runs `loss.backward()` for all gradients, then **Adam optimizer** updates parameters. Adam tracks moving averages of gradient direction (momentum) and magnitude — the same optimizer behind GPT-4 and DALL-E training.

### 6. Inference — Generating Names

Start with BOS, sample next token from probability distribution, feed prediction back in, repeat until EOS. **Autoregressive generation** — the exact same process ChatGPT uses every time you send a message.

![](/images/blog/-198-lines-are-all-you-n-3.webp)

---

## Why This Matters — By the Numbers

| | PyTorch + HuggingFace | Karpathy's 198 Lines |
|--|--|--|
| Dependencies | Dozens | **Zero** (pure Python) |
| Lines of code | Thousands | 198 |
| Comprehensibility | Low | High |
| Performance | Production-grade | Educational |
| Conceptual clarity | Low | **Maximum** |

As Karpathy put it: *"This is the full algorithmic content of what is needed. Everything else is just for efficiency."*

Frameworks exist for optimization and convenience — they're wrappers. What happens inside is still just math and code.

---

## A Memory from the Broad Institute

Reading this code pulled up an old memory.

When I was a visiting PhD student at the **Broad Institute of MIT and Harvard**, my task was to implement **a single line of PyTorch in C** — for multi-party computation research.

Since we needed deep learning operations to run on *encrypted data*, hiding behind framework abstractions wasn't an option. I had to go back to first principles.

**Weight initialization** from scratch. Xavier and He init, derived from equations and written directly in C. **Activation functions** linearized — GELU approximated as a polynomial, with careful tracking of how approximation error propagated through training.

![](/images/blog/-198-lines-are-all-you-n-4.webp)

Then there was **backpropagation**. Working with the math library, Eigen for matrix ops, and Boost for utilities, I derived gradients by hand and translated them into code. Everything had to account for network communication costs. Compile, build, debug, repeat — in C, considering actual network topology.

It took weeks. But what I got out of it was something no tutorial could give me: **complete intuition for how deep learning actually works.**

---

## A Question for Today's AI Engineers

Honestly — how many AI developers today have **trained an MLP from scratch**?

Fine-tuning? Plenty. RAG? Everywhere. LLM API calls? Of course. But actually implementing backprop, watching the gradients flow with your own eyes?

Building and debugging in C while accounting for network latency?

This isn't nostalgia. This is a real concern. **As AI tools get more powerful, the gap between people who understand the fundamentals and those who don't will only widen.**

![](/images/blog/-198-lines-are-all-you-n-5.webp)

Consider: why does adding attention heads improve performance up to a point, then hurt it? Why do you need learning rate warm-up? What does weight decay actually do to prevent overfitting? If you have genuine intuition about these things, you tune hyperparameters differently. Not "this worked in the experiment" — but "here's *why* this is the right direction."

---

## What 198 Lines Actually Reveals — Karpathy's 6-Year Compression

This didn't come out of nowhere. Karpathy has been peeling away layers of abstraction for six years:

- **2020**: `micrograd` (autograd engine)
- **2020**: `minGPT` (PyTorch GPT)
- **2023**: `nanoGPT` (production-grade training)
- **2024**: `llm.c` (raw C/CUDA, no frameworks)
- **2026**: `microGPT` (**the algorithm and nothing else**)

Each step removed a layer. This final version removed all of them.

**GPT's fundamental complexity is lower than most people assume.**

The transformer breakthrough is a combination of a few key ideas:
1. Self-attention: direct connections between arbitrary positions in a sequence
2. Residual connections: guaranteed gradient flow
3. Layer normalization: training stability
4. Massive scale: data + parameters

Once you genuinely understand these four, the difference between GPT-2 and GPT-4 is structural, not conceptual — more layers, more heads, more data. Same ideas, bigger numbers. The industry is spending $400 billion on AI infrastructure this year. But the core algorithm powering all of it fits in a file smaller than most READMEs.

![](/images/blog/-198-lines-are-all-you-n-6.webp)

---

## Should You Read It?

**Yes. No caveats.**

Whether you're using AI as a tool, aiming to become an ML researcher, or building on top of LLM frameworks professionally — this code is worth your time.

Karpathy's 198 lines beats most textbooks. You can watch equations become code become output, all in a single file.

I'm planning to read through the whole thing this weekend — with the Broad Institute memories running in the background. Back then, I wondered why I was putting myself through all that. Now I'm just glad I did.

![](/images/blog/-198-lines-are-all-you-n-7.webp)

---

## Closing Thought

AI tooling keeps improving. Copilot writes the code, Claude designs the system, Cursor suggests the refactor. That's genuinely good.

But if you're using tools without understanding what they're doing, you eventually hit a wall: "This seems like it should work — why is it producing garbage?" And you have no way to answer that.

**198 lines of Python is the antidote to that wall.**

Go read it. Seriously.

---

**References:**
- [Andrej Karpathy's microGPT — GitHub Gist](https://gist.github.com/karpathy/8627fe009c40f57531cb18360106ce95)
- [Sumit Pandey's code walkthrough — Towards Deep Learning](https://www.towardsdeeplearning.com/andrej-karpathy-just-built-an-entire-gpt-in-243-lines-of-python-7d66cfdfa301)
