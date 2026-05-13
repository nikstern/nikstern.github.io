---
layout: post
title: "A world of agents: how did we get here?"
date: 2026-04-02 15:36:28 -0700
categories: notes
---

## Overview

A lot of people are being affected by AI without a background in AI concepts, making the transition more jarring and confusing. This post describes the concepts and milestones that led to LLM agents. I've tried to keep it as approachable as possible for people from varying technical backgrounds.

If there are points where I lose you, feel free to comment. On the flip side to that, while seeking to abstract and explain, I'm sure I may have overly reduced certain concepts or made mistakes. If you'd like to clarify/correct a point, comment as well.

At sufficient scale, LLMs became surprisingly capable of producing useful responses to general tasks and questions. However, that output is just text: an LLM is not editing your filesystem. Software harnesses interpret LLM output and use it to decide actions to take next. LLMs became more reliable at producing output that can be translated into useful text and actions by harnesses.

## AI: Rule-Based vs Machine Learning

The rule-based AI approach "hard-codes" rules and patterns to follow, whereas machine learning tries to get AI systems to "learn" more "organically." These fields have argued for ~75 years, but there are many ways in which they can be combined together.

The argument goes like this:

- Rule-based: "You cannot rely on statistical behavior to perform expert actions!"
- Machine-learning: "Give us more compute and data and we can get there!"
- Rule-based: "But you aren't there yet!"

I specialized in rule-based AI. I went into school/research when machine learning was becoming more practical, but not widespread. I ended up working on several things which ended up using a combination of both.

Now I'd see myself as being somewhere in the middle: encoding expert workflows to "rein in" machine-learning models. I feel it allows us to meet where AI is at today, but others may disagree.

## Neural Networks

Where rule-based systems tend to fail is that it is often impossible to directly program a correct output for every single scenario.

Essentially the goal of a huge neural network is to try to "learn" to produce a correct output for any input.

Inside a neural network is a series of layers and nodes (parameters/weights). Think of inputs as moving through those layers and being shuffled along weights that move it toward a hopefully correct output.

As the network is "trained", it tunes those layers and weights based on feedback. When the feedback is good, it tries to repeat that movement more often. When the feedback is bad, it tries to adjust to do it less.

The idea with neural networks is that if you give it enough data about the world, and enough different nodes, it can learn by itself to always move those inputs to the correct output.

One of the main applications of neural networks has been natural language processing, which is the ability to produce useful output from an input of human text or speech. You can go very far back with the ways people have been fascinated with or have attempted text/story/sentence generation, for centuries. We will focus on more direct concepts/precursors most related to LLMs. This subject tends to be math heavy and technical, I will simplify it as much as I can.

## Tokens

Despite the name, Large Language Models (LLMs) do not "understand" language as we do. They are trained to model relationships between tokens. Tokens are groups of characters, not necessarily words or ideas.

![From Hugging Face, visualizer for the tokenization process](/assets/images/a-world-of-agents-how-did-we-get-here/a-world-of-agents-how-did-we-get-here-000.png)

> From Hugging Face, visualizer for the tokenization process

### Prompt input to output

A text prompt is "tokenized" into a sequence of tokens, as shown above. These tokens end up being stored as numbers. What the LLM is actually passed as input is something like:

```text
[43432,5775,...7345,6566]
```

The point of a model is to produce a distribution of likely next tokens.

When the model receives the input, "Datadog is a", it returns something like:

- 50% chance of "company"
- 25% chance of "SaaS"
- 15% chance of "observ"
- 10% chance of "vendor"

When you send a prompt to an LLM provider, the provider repeatedly runs generation steps and selects a next token:

1. "Datadog is a"
2. "Datadog is a company"
3. "Datadog is a company that"
4. "Datadog is a company that provides"

Sometimes the next token selected is a special stop signal, which causes the loop to end. LLMs will sometimes go on and on without producing that signal, which causes the long, rambling outputs you sometimes see. As you can tell, I tend to do the same thing.

## Earlier text generators

For several decades the main approach to text generation was using Recurrent Neural Networks (RNNs). RNNs need to sequentially process each token of their input in order to start predicting their output tokens. Training needs to happen in sequence as well. It was not possible to be done in parallel. A very long input was very slow to process. RNNs also often had problems with processing relationships between tokens far apart from each other.

The combination of sequential processing and weak coherence between different parts of the output made very long outputs slow and sometimes incoherent.

## So What Happened?

In 2017, several scientists at Google published a paper describing a new "transformer" architecture based around a mechanism introduced in 2014, called "attention".

While RNNs required sequential processing, attention can be done in parallel. Attention is also much better at computing relationships between all the tokens in a long input. Those relationships mean that all of the tokens in its input are more often "considered" at once when determining an output. In practice, the output of an LLM is more likely to be related to everything in the input.

Previously, due to their sequential nature, RNNs needed to be trained on much smaller and more specific datasets. Attention/transformer-based models started outperforming leading RNNs at natural language in a larger variety of language domains.

When a model is trained, it stores relationships between token inputs in its parameters and adjusts them over time. With only a few parameters, those relationships have to be represented with a very small amount of data. GPT-1 had 117 million parameters. OpenAI then scaled further, releasing GPT-2 in 2019 with 1.5 billion parameters. OpenAI released this model in stages, due to concerns over the possible societal impacts of cheap, "fake", and unreliable text generation.

Model size kept increasing: GPT-3 came out in 2020 with 175 billion parameters. It later released an optimized version of this model as GPT-3.5, alongside an app to speak to it, ChatGPT.

More parameters allow for more complex relationships to be stored about more tokens. (The relationship here is actually more complicated, but this is meant to be a simple introduction.) For example it could store that "Einstein" has a relationship to "Hawking" even if it never saw the two in the same sentence.

As early as GPT-1, OpenAI started remarking on an important and unexpected result that led us to where we are today:

- When trained on a very large dataset with many parameters, neural networks can produce coherent responses on subjects that they were not explicitly trained for (less parrot-like than earlier networks).
- That they needed a lot of compute to go bigger.

## GPUs

If you run the attention mechanism on a single processor, it actually uses more time and memory than RNNs. Machine learning is based on complex math that in order to process large inputs, needs to be very parallelized.

Computer hardware experts have been improving mechanisms to perform these operations since the 1960s because they are central to computer graphics rendering. As computer graphics grew more complex, specialized hardware for performing parallel graphical computations were developed: GPUs.

To deal with the amount of operations required for training and inferring for really big models, massive amounts of GPUs are required. When it's not being parallelized, long inputs get very slow and memory intensive. Massive amounts of training and inference have crashed the supply chain for RAM and GPUs.

## Why code?

Code turned out to be a more natural fit for LLM generation due to the strong relationships between its tokens. Training and inference work best when there are consistent patterns in training data and intended output.

For example, while training on data from software repos and the internet, a model is going to "see" variable declaration and assignment over and over again.

```text
<type> <name> = <value>
```

When it comes time to infer correct code, a line for variable assignment is going to follow that same pattern, even if the type, name, and value are different than the training data.

Unlike complex natural prose, LLMs can better predict things like a closing brace following an open brace, a declared variable being assigned after declaration, etc.

From 2021 to 2024, there was a slow progression of an LLM model's ability to generate code. IDE integration was possible using GitHub Copilot (based on a version of GPT-3 called OpenAI Codex) and Cursor which provided line completion, file scaffolding, and some generation of common patterns. However, this code tended to be rudimentary, localized to common use cases, and highly prone to error. While there were syntax relationships, relationships between long chains of lines of code were more difficult to represent.

## Adding business context

In 2024, developers still typically interacted with a browser interface such as ChatGPT, creating a layer of separation between the code generated and the developer's workspace.

AI users often want to define custom tools and workflows specific to their use case. Though introduced in 2020, RAG (Retrieval Augmented Generation) gained renewed interest as a way to add context on top of a model's training.

In 2024, Anthropic announced MCP (Model Context Protocol) as an API layer to connect models to external context sources. This led to a race for many SaaS companies to introduce "AI-native" capabilities by announcing their own MCPs.

However, an MCP being accessible to an LLM and being "AI-native" is a marketing term. Anyone can make an MCP and have it return any kind of data, regardless of whether it is actually optimized for LLMs. Keep in mind that the exact relationship between what the MCP returns and what it causes the LLM to output is largely unknown. Many implementations were "best guesses" at what might be helpful to an LLM.

Anthropic's Claude Code integrated Anthropic models into the terminal with a set of tools to directly read, write, and execute code in the codebases that an engineer works in. Claude Code was not the first to do this, but was the first to gain widespread popularity. Similar applications were then launched by many major LLM providers.

## Agents

Agents are "software systems that use AI to pursue goals and complete tasks on behalf of users." The work of building systems that turn model output into useful actions is often called harness engineering.

LLM agents typically use a harness to follow a loop of gathering context, planning, acting, and evaluating before returning a result.

A model can be invoked at any point in this process for varying purposes and with different prompts. The model might be asked to generate the plan, list an appropriate tool call, determine an end state through examination of tool outputs, etc. Different parts of this loop can be deterministic or based on the LLM.

A coding harness doesn't mechanically change an LLM. An LLM model is stateless and only produces probabilities for the next token to generate. They do not take actions or "remember" conversation history. Stepping through this loop, gathering and holding context, and performing actions are the responsibility of the harness, such as Claude Code, rather than the LLM.

2025 saw a rapid progression in models' ability to produce quality code. Anthropic's Claude Opus 4.5's launch in November represented a huge shift in agents' capabilities to create not just code or files, but complex software systems. Agentic coding, the use of AI to plan, execute, and test releasable software saw a dramatic shift in feasibility.

Over time, additional tooling such as Skills have created new standards that allow coding harness users to easily define new tools.

The impact of RAG, MCPs, skills, and memory systems on agent performance is still not fully understood. Many implementations can hurt agentic performance rather than improve it.

## Agents Everywhere

Claude Code was originally intended for code. However, users of Claude Code found that if you added access to documents, images, APIs, and files you could get it to do all sorts of knowledge work.

The ability of LLMs to produce massive amounts of generated output and perform risky actions has caused severe problems. At this point, agents are able to generate large, complex outputs that are very difficult for a human to review or reason about. Getting LLMs to check their work is often a circular loop of needing to check whether they checked their work correctly. The bottleneck is no longer creating output, but providing correct, maintainable behavior.

Personally, I think that, for now, progress towards complex behaviors depends on harness engineering. One day, more compute and more efficient algorithms may make this work obsolete, and I'm okay with that.
