---
layout: post
title: "Anatomy of a Chatbot"
date: 2026-05-13 15:50:38 -0700
categories: notes
---

AI attribution: none.

This post describes the architecture and some of the internal mechanisms of an LLM-backed chatbot. Chatbot architectures share several concepts with agentic harnesses, so this content is a basis for further discussion of building agentic systems.

> The components discussed in this post are representative of how chatbots/agents work but not exact due to there being many different options for naming/implementation. The boxes in the diagrams may all be a part of one function, or separated into various names/modules. They may have custom implementations, be a library call, be deterministic, non-deterministic, etc.

I'm defining a chatbot here (others may define it differently) as software geared towards receiving a natural language prompt and returning a text response. For it to be a chatbot and not an agent, the actions that the chatbot takes are read-only. There are no changes to external systems in order to return the chatbot's response.

Most people's first exposure to an LLM chatbot was through ChatGPT:

![The classic chatbot. User sends a prompt to the web interface, the model generates and returns a response.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-000.png)

In the previous post, we discussed some basics of LLM tokenization and generation. Some key aspects:

- Prompts and "context" are broken up into tokens, which are the input to an LLM.
- The output of an LLM call is a probability distribution for what the next token might be.
- The LLM is called in a loop until a special stop signal is received.
- Those tokens are parsed back into characters and sent to the user.

I will call this the core loop:

![The user sends a prompt, and the chatbot software loops until a stop signal is received, and sends the final output.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-001.png)

This post is going to focus on understanding the output and context building portions. The details of the model/inference aspect is more technical than I'd like to talk about here.

If you'd like to learn about those technical aspects, I've found the book in this post to be useful. Note that the company may keep emailing you after you sign up for their book.

## Input

In the simplest case, a prompt passes through a tokenizer and is passed to a model.

![A prompt passes through a tokenizer and is passed to a model.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-002.png)

This would work if you wanted a very minimal, single prompt/response chatbot. There's no conversation history, no system prompt, just getting the direct response from the model.

For a chatbot to be an assistant, this won't be very useful.

## Output

Each time the output returns a token that is not a stop signal, it is appended to the end of the previous input, then sent to the model again:

![The streaming response happens by sending out each de-tokenized output as it comes out until the stop signal is reached.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-003.png)

By default, an LLM is going to give you the probability distribution for the most likely next token after the prompt. We covered this in the last post, but to briefly recap:

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

Sometimes the next token selected is a special stop signal, which causes the loop to end.

However, this isn't always conducive to functioning as an assistant rather than an "autocomplete." For example, in response to the prompt:

> "I would like to know more about LLMs"

The final response back with no system prompt might be:

> "so that I can use them for work."

The LLM needs context that shapes its generated tokens into a conversational back and forth. This is the role of the system prompt.

## System Prompt

The system prompt establishes the initial context, instructions, and intended requirements for an LLM. It "sets up the scenario" in order to try and make the LLM's output conform to the intended behavior for the LLM-powered application. In the case of a general purpose chatbot, the system prompt often starts with something like this:

> "You are a friendly assistant..."

Anthropic has made many of their system prompts public over the last several years. Over time, they've tended to grow longer. Let's look at a simple one from Haiku 3 in 2024:

```text
The assistant is Claude, created by Anthropic. The current date is
{{currentDateTime}}. Claude's knowledge base was last updated in August
2023 and it answers user questions about events before August 2023 and
after August 2023 the same way a highly informed individual from August
2023 would if they were talking to someone from {{currentDateTime}}. It
should give concise responses to very simple questions, but provide
thorough responses to more complex and open-ended questions. It is
happy to help with writing, analysis, question answering, math, coding,
and all sorts of other tasks. It uses markdown for coding. It does not
mention this information about itself unless the information is
directly pertinent to the human's query.
```

For length comparison, check the Claude 4.7 system prompt.

Notice that there are variables being passed in. Once there are multiple sources of context and differences between instructions, prompt, and response, some additional component is required, which I will call a bundler. This component is more mysterious than others because it is not always shared publicly and can be implemented in a variety of ways. However, something needs to fill in variables and provide some sort of structured format:

![The bundler creates a structured final input to the tokenizer from the combination of different context sources.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-004.png)

For example, the bundler might replace placeholders and produce something like the following as an input to the LLM:

```text
Instructions:

The assistant is Claude, created by Anthropic. The current date is May
13th, 2026. Claude's knowledge base was last updated in August 2023 and
it answers user questions about events before August 2023 and after
August 2023 the same way a highly informed individual from August 2023
would if they were talking to someone from 2026. It should give concise
responses to very simple questions, but provide thorough responses to
more complex and open-ended questions. It is happy to help with
writing, analysis, question answering, math, coding, and all sorts of
other tasks. It uses markdown for coding. It does not mention this
information about itself unless the information is directly pertinent
to the human's query.

Prompt:

What is Datadog?

Response:
```

Over time models have been trained to better conform to this kind of structure, "recognizing" that it should produce "chatbot-like" responses, so it will produce something like:

> Good question. Datadog is an observability vendor that...

At this point, we'd have a chatbot-like response with this setup. However, each prompt would have no context for anything that previously happened in the conversation.

## Conversation History

LLMs are stateless. If we want it to have a "history", we need to pass it in as part of the input. Typically, the conversation history is passed in as a structured (~JSON) set of `prompt`, `response` keys and values to the context bundler.

![A diagram from Anthropic representing how it passes its conversation history and its relationship to the context window.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-005.png)

> Diagram source, Anthropic

The conversation history is a further piece of context passed into the context bundler system.

![Conversation history is passed into the context bundler system.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-006.png)

At this point, when implemented, you'd have the ability to run the chatbot in a session/conversation.

## Attachments

Text based attachments can be added to the bundler as well, assuming the text can be extracted. Image or other types of content moves into a whole new ranges of complexity/models that shouldn't be covered in this post.

![The text/content of file attachments are processed before adding them to the bundler.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-007.png)

## Conclusion

There you have it, the basics of how a text-based chatbot works:

![A context builder gathers all necessary tokens for the model, and gathers the output in a loop until a stop signal is reached.](/assets/images/anatomy-of-a-chatbot/anatomy-chatbot-008.png)

A context builder gathers all necessary tokens for the model, and gathers the output in a loop until a stop signal is reached.

At this point, you'd have a decent chatbot implemented. Notice that at this point, other than the model, there are no external systems touched by the chatbot application. Coming up, we'll discuss concepts such as MCP, RAG, and tool use as we construct more detailed agent harnesses.
