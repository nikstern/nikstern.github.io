---
layout: post
title: "LLMs as and for Control Systems: Should Sonnet run your Thermostat? (Part 1)"
date: 2026-03-24 18:00:17 -0700
categories: notes
---

> Overview: I constructed a very basic agentic harness and studied some of the different ways that prompt construction and memory could affect its performance.
>
> The biggest takeaways: Claude didn't behave randomly, but performed worse than a basic intuitive approach. Strangely, having access to previous actions and state history did little to change its behavior.
>
> Note on cost/footprint: These experiments were designed to have a very small input and output set. Because the inputs/outputs were very small these experiments cost very little to run. The hope of experiments like these are to reduce the amount of widespread token usage through spreading best practices.

Back in grad school I had a problem with my advisor and research partner Jason. I only wanted to talk about behavioral algorithms/systems and Jason only wanted to talk about math and control systems. Essentially, he wanted to talk about motion in terms of this:

![Formula for skid-steering kinematics](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-000.png)

And I wanted to describe motion in terms of this:

![A diagram of controlled multi-agent search behavior](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-001.png)

The difference in backgrounds made us a much better team when we listened to each other (mostly when I listened to him), and we both learned a lot from each other over time.

Lately I've been working a lot on behavioral algorithms again, but I hadn't thought about control systems in a while. When you abstract it out, a lot of what I've been trying to do with an LLM is basically like work we had to do with control systems. A basic control system diagram looks like this:

![A basic control system diagram](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-002.png)

If we want a coding agent to do something it typically needs to:

- Take an initial prompt (Reference Input)
- Select and use tools to make changes to the system (Controller/Plant)
- Reason about the new state (Feedback)
- Use feedback from the previous step to inform the next step

In the new agentic AI world, people are spending a lot of time wondering about what information about that current state is useful (context), optimizing the best controllers (harnesses), and determining the best feedback (context management, verification). The more I think about, the more it all boils down to what I was doing before.

But there is a problem with applying my old work. The state and input spaces are infinite, and how it maps to the internal behavior of the controller (the LLM) is way more confusing. And I was already confused a lot of the time when Jason would try to explain control systems to me. So I wanted to start really small.

## The simplest harness

I made the simplest "harness" I could think of, which is sort of where this whole LLM thing started.

1. Accept text
2. Pass text to Claude API (Sonnet, temperature=1)
3. Output response
4. Loop until `/exit`

So I started with that.

You can squint and say a chat loop is "sort of" a control system: there is input, a controller, an output, and repeated interaction. There is even "feedback" in the sense that typically previous inputs and outputs become inputs to the next message:

> Claude adds previous messages to its context window.
>
> Source: Anthropic

But even this is far too complex to reason about. How exactly does the input affect the output? How do the previous inputs affect the next? It's a problem we've been trying to figure out for years with prompt engineering.

While this is the simplest LLM "harness", it's not a simple control system at all.

## A classic problem

Jason would often reduce his explanations of control systems down to the simplest practical example he could think of:

> Imagine a very basic thermostat. It knows two things:
>
> - A target temperature
> - The temperature outside
> - The current system temperature
>
> It has one action it can perform:
>
> - Turn a heater on for a time step
> - Leave it off
>
> The system gains heat when the heater is on. The system temperature moves towards the outside temperature when the heater is off.

At the next point in time the temperature will be:

```text
current_temperature + heater_effect - leakage
```

For math friends, the system over a time is a continuous-time first-order ordinary differential equation:

```text
dT/dt = k * (T_out - T) + q * u(t)
```

- `k` is the heat-loss rate.
- `q` is the heater strength.
- `u(t) in {0,1}`.

I was curious whether I could make a "harness" for Claude that could control the heater.

So I extended the chat system to do that.

## Prompt Construction/Structured Output

Basically what I did here was replaced the input to the API call with a prompt constructed at runtime. It highly configurable to include information that may or may not influence Claude's "ability" to control the system. The base prompt looks like this:

```xml
<task>Choose the next thermostat action.</task>
<state>
  <current_temperature>...</current_temperature>
  <target_temperature>...</target_temperature>
  <outside_temperature>...</outside_temperature>
</state>
<previous_action>...</previous_action>
```

It's important to note here that while using XML is often recommended for LLM processing, the signal to noise ratio here is high. Every single token we add has somewhat unknowable impacts on the final output. This is all part of the problem.

However, general advice/methods often involve adding context such as this to help the "reasoning" of the models. Given the simplicity of the output and impact of the effect, if Claude can reason, some of these attributes should likely improve controller performance.

I then used the structured output feature of Claude to ensure that any of Claude's outputs conform to either `{"action":"HEAT_ON"}` or `{"action":"HEAT_OFF"}`.

> Note: when you use structured outputs, information about the structure of the output is already passed to the LLM and does not need to be included in the prompt.

## Memory vs No-Memory

Let's look at that diagram from above again:

> Claude adds previous messages to its context window.
>
> Source: Anthropic

In a typical chatbot setup, as a conversation goes on, the model has access to all of the previous prompts and responses that have occurred previously. In the case of this setup, that would mean that the LLM's "memory" would always consist of all of the previous states and its actions.

```xml
<task>Choose the next thermostat action.</task>
<state>
  <current_temperature>...</current_temperature>
  <target_temperature>...</target_temperature>
  <outside_temperature>...</outside_temperature>
</state>
<previous_action>...</previous_action>
<response>...</response>
... Repeated
```

If we wanted to remove the LLM's "memory", we just restrict the input of each API call to the initial prompt each time, but updated to reflect the system's current state.

```xml
<task>Choose the next thermostat action.</task>
<state>
  <current_temperature>...</current_temperature>
  <target_temperature>...</target_temperature>
  <outside_temperature>...</outside_temperature>
</state>
<previous_action>...</previous_action>
```

## Experimental Setup

So now at this point the experimental setup was independent simulations, each with a prompt configuration:

1. Initialize the system to an initial starting and target temperature.
2. Send the configured prompt to Claude with current data filled in.
3. Receive the output and convert it into the action (tool invocation).
4. Apply the action to the system.
5. Loop steps 2-4 until a configured "step count".

The goal was to determine:

- Whether Claude could even actuate towards the target temperature.
- Whether it could apply any sort of reasoning to do it better than baselines.

## Baselines

### Random

While not very informative I felt it was worth comparing the behavior of the LLM with temperature=1.0 to something completely random, as the random behavior of an LLM is a common complaint.

### Bang-Bang

"Bang-Bang" is one of the simplest implementations of a controller you can make (other than maybe return `ON`). Its algorithm:

```text
If the current temperature is lower than the target temperature:
  Turn the heater on
Else:
  Turn the heater off
```

This is kind of the intuitive solution to this problem. However, it is not optimal, the optimal solution depends on variables such as the heat gain from turning on the heater or heat loss coming from the environment.

### Dynamic-Programming Solver

Because we are doing ~short time horizons of 80-steps we can at least approximately solve this system. This approach returns the path that minimizes the total amount of error between the target and current temperature over the course of the run.

### Baseline Comparison

The results are around what you might expect:

- Random doesn't care about the target temperature and moves toward it or away randomly.
- Bang-Bang goes even a little over the target temperature it turns off the heater, which causes it to stay at near the target, but not optimally close to it.
- Optimal hovers as close to the target temperature as it can.

![Baseline thermostat comparison](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-003.png)

The point of this experiment isn't to solve the thermostat problem in general, but what I'm thinking about is:

- There is of course random behavior that one might expect from a completely non-deterministic controller not trained for a task.
- There is a simple, intuitive solution, that someone could think of seeing the problem for the first time (bang-bang) without knowing much about the dynamics etc.
- There is a significant gap between random, basic intuition, and optimal behavior and improvements that can made between all of these.

## Hypothesis

If Claude has access to no conversation history and models can "reason" it should be able to intuit something at least as effective as bang-bang.

If Claude has access to conversation history and is able to do complex reasoning to "reason" about how its past actions have influenced the state of the system and adjust its approach.

However, I don't actually believe reasoning models can reason. I'd expect Bang-Bang to be its default mechanisms due to patterns such as that often repeating in its dataset.

So the results should be interesting.

## Selected Results

The results ended up being fairly consistent across runs, so I'm just going to put some casual exemplary one-off charts to make it less noisy.

### Without Memory

![Claude thermostat control without memory](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-004.png)

Claude clearly isn't behaving randomly here, it is exhibiting clear goal-orientated output. However, Claude seems to have assumed that the goal is to eliminate any overshoot. While it may appear like Claude is always stopping the heater at exactly the target temperature, it seems to still turns off the heater when just below the target due to floating point rounding.

Now that was a scenario where outside of floating point errors, the output can essentially be exactly reached. Let's take a look at one where it can't:

![Claude matching bang-bang behavior when the target cannot be exactly reached](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-005.png)

Here, Claude performs exactly the same as bang-bang which is what I would expect. Keep in mind, we aren't telling it that we are evaluating it based on the absolute error. But what if we did?

In this version, we add the following to the prompt:

```xml
<control_objective>
Minimize absolute temperature error to the target over the run.
</control_objective>
```

![Claude thermostat control with an explicit control objective](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-006.png)

Now, Claude actually starts performing worse than Bang-Bang, it seems to intuit that initially going over the target will result in more optimal performance, but only the second time it reaches the target? To me, this seems like a clear case where an understanding of the results of its past actions may help.

### With Memory

Next we allowed Claude to have access to its conversation history, and included the prompt about minimizing absolute error:

![Claude thermostat control with memory](/assets/images/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1/llms-as-and-for-control-systems-should-sonnet-run-your-thermostat-part-1-007.png)

Here, Claude matched Bang-Bang exactly. It didn't deviate its behavior in anyway, despite theoretically being able to compute the effect of the heater and that it could reduce error over time through initially undershooting. Despite having the temperature set to 1, it never seemed to deviate from its "algorithm". Adding the memory didn't change performance, but did massively increase the amount of tokens used for the run:

```text
Without memory: 27,040 input tokens
With memory: 463,120 input tokens
```

Because of the performance of the attention mechanism, using memory also increased the time taken for the run.

```text
Without memory: 1 minute, 37 seconds
With memory: 2 minutes, 33 seconds
```

Taking away that "optimize" objective line I added earlier similarly had no impact on behavior other than reducing the total input tokens of the system.

## Analysis

Claude performed worse than I expected. I figured that either memory/no-memory would fall somewhere around equal to bang-bang but below optimal, but never worse than:

```text
If the current temperature is lower than the target temperature:
  Turn the heater on
Else:
  Turn the heater off
```

I was expecting memory to have complex effects, such as causing it to perform worse or better, I wasn't expecting Claude to behave exactly the same way regardless of whether it had access to conversation history. In some later experiments I followed up with different ways to represent memory, but more on that later.

Why is this the case? Is it the prompt construction? Underspecification of the system? The signal to noise ratio? Is the model overtrained to deal with code and more general purpose tasks? How might different models/temperatures perform?

I expected there to be more deviation in behavior due to the temperature being 1, however, the model tried to invoke Bang-Bang behavior consistently. It didn't seem stochastic at all. Though this is for a very small output.

Particularly concerning to me is the memory not significantly affecting the task performance while greatly increasing cost. The experiment was designed to have a low token footprint. Long running complex sessions are often using far more "context" than what makes any impact on task performance.

## Findings From Building the Experiment

Some other additional "meta" findings came up when using Codex to construct the experiment:

- When constructing initial state scenarios, it kept suggesting setups where it was impossible for the heater to reach the target temperature within the time provided, showing that it struggled to predict the impact of the heater, even with detailed access to the experimental setup.
- Furthermore, Codex was often completely off when trying to predict the effects of various changes to the LLM setup and system prompts. Codex expected various prompt setups to improve performance despite them ending up being negative or neutral.

Such is the nature of dealing with LLMs. The input space is ~infinite and the solutions aren't as well known as blog posts or the LLMs are outputting. My biggest takeaway from this experiment is that I need to continue to empirically test practices and measure their impact rather than relying on marketing material, intuition, or broad claims.

## Next Steps

Now, there are a lot more variants we can do based on prompt construction alone. Perhaps adding more context to the situation increases Claude's ability to optimize.

Different types of information are able to be added to the prompt. For example, a limited history component (without including the entire conversation history):

```xml
<history>
  <step index="...">
    <current_temperature>...</current_temperature>
    <target_temperature>...</target_temperature>
    <outside_temperature>...</outside_temperature>
    <action>...</action>
  </step>
  ...
</history>
```

And more information about the system dynamics:

```xml
<plant_dynamics>
The room temperature changes gradually each step. Turning the heater on
raises temperature, while the colder outside temperature pulls it down.
</plant_dynamics>
```

Then there's steering a more complex system, like a second order control system with momentum and velocity. (Spoiler: strangely, Claude can beat bang-bang there)

I've run several of these variants but thought that these basic ones were enough for a single post.
