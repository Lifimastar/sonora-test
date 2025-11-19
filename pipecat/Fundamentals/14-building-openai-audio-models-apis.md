# Building With OpenAI Audio Models and APIs

> Create voice agents with OpenAI audio models and Pipecat

This guide provides an overview of the audio capabilities OpenAI offers via their APIs. We'll also link to Pipecat sample code.

## Two Ways To Build Voice-to-voice

You can build voice-to-voice applications in two ways:

1. The cascaded models approach, using separate models for transcription, the LLM, and voice generation.

<Frame><img src="https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-cascade.jpg?fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=e2e389318021ff76c15da1734c28d49d" alt="OpenAI Cascaded Pipeline" data-og-width="2877" width="2877" data-og-height="868" height="868" data-path="images/openai-cascade.jpg" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-cascade.jpg?w=280&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=2ca91677fd50766e17d22df889b03678 280w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-cascade.jpg?w=560&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=1d4cbb071ef2ba79bcf7044a725d2ab8 560w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-cascade.jpg?w=840&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=339ce699cfbdc88094b8ca90a5e699f8 840w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-cascade.jpg?w=1100&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=bab07cf5169f9b0003260f4163cb348b 1100w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-cascade.jpg?w=1650&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=1a03211a75161830777a34500702fe5a 1650w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-cascade.jpg?w=2500&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=09f5c4be9ce33ddd98627188e805e836 2500w" /></Frame>

A cascaded pipeline looks like this, in Pipecat code. Here's a [single-file example that uses a cascaded pipeline](https://github.com/pipecat-ai/pipecat/blob/main/examples/foundational/07g-interruptible-openai.py). (See below for an overview of Pipecat core concepts.)

```python  theme={null}
pipeline = Pipeline(
    [
        transport.input(),
        speech_to_text,
        context_aggregator.user(),
        llm,
        text_to_speech,
        context_aggregator.assistant(),
        transport.output(),
    ]
)
```

2. Using a single, speech-to-speech model. This is conceptually much simpler. Though note that most applications also need to implement things like function calling, retrieval-augmented search, context management, and integration with existing systems. So the core pipeline is only part of an app's complexity.

<Frame><img src="https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-s2s.jpg?fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=a28ba89b79e0fafb91775bf572e3eac5" alt="OpenAI S2S Pipeline" data-og-width="2877" width="2877" data-og-height="868" height="868" data-path="images/openai-s2s.jpg" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-s2s.jpg?w=280&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=faeabe5c34f66148011561de5e349e56 280w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-s2s.jpg?w=560&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=353f953d2464947c780ab8b4983edaad 560w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-s2s.jpg?w=840&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=8d482bcbe3227763c975063cbb45e3f8 840w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-s2s.jpg?w=1100&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=5ef9f830148f10e9304ebc85701c0b77 1100w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-s2s.jpg?w=1650&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=c0cd04809992dd8c2c5f391b5edefb09 1650w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-s2s.jpg?w=2500&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=67d1da965ce7efa8ae60e6eb39835819 2500w" /></Frame>

Here's a speech-to-speech pipeline in Pipecat code. And here's a [single-file example that uses the OpenAI Realtime API](https://github.com/pipecat-ai/pipecat/blob/main/examples/foundational/19-openai-realtime-beta.py).

```python  theme={null}
pipeline = Pipeline(
    [
        transport.input(),
        context_aggregator.user(),
        speech_to_speech_llm,
        context_aggregator.assistant(),
        transport.output(),
    ]
)
```

Which approach should you choose?

* The cascaded models approach is preferable if you are implementing a complex workflow and need the best possible instruction following performance and function calling reliability. The `gpt-4o` model operating in text-to-text mode has the strongest instruction following and function calling performance.
* The speech-to-speech approach offers better audio understanding and human-like voice output. If your application is primarily free-form, open-ended conversation, these attributes might be more important than instruction following and function calling performance. Note also that `gpt-4o-audio-preview` and the OpenAI Realtime API are currently beta products.

## OpenAI Audio Models and APIs

### Transcription API

* Models: `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`
* Pipecat service: `OpenAISTTService` ([reference docs](/server/services/stt/openai))
* OpenAI endpoint: `/v1/audio/transcriptions` ([docs](https://platform.openai.com/docs/api-reference/audio/createTranscription))

### Chat Completions API

* Models: `gpt-4o`, `gpt-4o-mini`, `gpt-4o-audio-preview`
* Pipecat service: `OpenAILLMService` ([reference docs](/server/services/llm/openai))
* OpenAI endpoint: `/v1/chat/completions` ([docs](https://platform.openai.com/docs/api-reference/chat))

### Realtime API

* Models: `gpt-4o-realtime-preview`, `gpt-4o-mini-realtime-preview`
* Pipecat service: `OpenAIRealtimeBetaLLMService` ([reference docs](/server/services/s2s/openai))
* OpenAI docs ([overview](https://platform.openai.com/docs/guides/realtime))

### Speech API

* Models: `gpt-4o-mini-tts`
* Pipecat service: `OpenAITTSService` ([reference docs](/server/services/tts/openai))
* OpenAI endpoint: `/v1/audio/speech` ([docs](https://platform.openai.com/docs/api-reference/audio/createSpeech))

## Sample code and starter kits

*If you have a code example or starter kit you would like this doc to link to, please let us know. We can add examples that help people get started with the OpenAI audio models and APIs.*

### Single-file examples

<CardGroup cols={2}>
  <Card title="OpenAI STT → LLM → TTS" icon="code" href="https://github.com/pipecat-ai/pipecat/blob/main/examples/foundational/07g-interruptible-openai.py">
    A complete implementation demonstrating the cascaded approach with OpenAI services
  </Card>

  <Card title="OpenAI Realtime API" icon="tower-broadcast" href="https://github.com/pipecat-ai/pipecat/blob/main/examples/foundational/19-openai-realtime-beta.py">
    A speech-to-speech implementation using OpenAI's Realtime API
  </Card>
</CardGroup>

### OpenAI + Twilio + Pipecat Cloud

[This starter kit](https://github.com/daily-co/pcc-openai-twilio/) is a complete telephone voice agent that can talk about the NCAA March Madness basketball tournaments and look up realtime game information using function calls.

<Frame>
    <img src="https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-twilio.png?fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=fcde44430a2b87c8467af8de0871fb24" alt="OpenAI Twilio" data-og-width="1598" width="1598" data-og-height="1284" height="1284" data-path="images/openai-twilio.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-twilio.png?w=280&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=05f08079f15eb0c0b6e15dda86c7c65b 280w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-twilio.png?w=560&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=94bcd70b14e4f5d361bff1842a99f578 560w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-twilio.png?w=840&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=3fa9a58977aeb866e43001346832f4c5 840w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-twilio.png?w=1100&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=af0fdc815aeca2417d96364d00a17092 1100w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-twilio.png?w=1650&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=af4f08d50588f303d81d83bf001aeaa3 1650w, https://mintcdn.com/daily/2bYrACcmgvvzC075/images/openai-twilio.png?w=2500&fit=max&auto=format&n=2bYrACcmgvvzC075&q=85&s=57142b67b5e8eb1338a4e8ff4bceb52c 2500w" />
</Frame>

The starter kit includes two bot configurations: cascaded model and speech-to-speech. The code can be packaged for deployment to Pipecat Cloud, a commercial platform for Pipecat agent hosting.
