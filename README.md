[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/jtlicardo/bpmn-assistant?style=social)](https://github.com/jtlicardo/bpmn-assistant/stargazers)
[![CI](https://github.com/jtlicardo/bpmn-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/jtlicardo/bpmn-assistant/actions/workflows/ci.yml)


![Logo](assets/bpmn_assistant_logo.png)

Describe a business process. Get a BPMN diagram.

[Try BPMN Assistant](https://bpmn-frontend.onrender.com)

![Purchase order process with message flows, a multi-instance task, and a text annotation](assets/app_screenshot.png)

## Quickstart

### Option 1: Use the hosted version

The easiest way to get started - no setup required!

Visit **[bpmn-frontend.onrender.com](https://bpmn-frontend.onrender.com)** and provide your own API keys directly in the interface. Your keys are stored locally in your browser and never stored on any servers.

### Option 2: Run locally with Docker

1. Clone the repository

```
git clone https://github.com/jtlicardo/bpmn-assistant.git
```

```
cd bpmn-assistant
```

2. Set up your environment variables

<details>
<summary>Linux, macOS</summary>

```
cd src/bpmn_assistant
```

```
cp .env.example .env
```

</details>

<details>
<summary>Windows</summary>

```
cd src\bpmn_assistant
```

```
copy .env.example .env
```

</details>

3. Open the `.env` file and replace the placeholder values with your actual API keys.

4. Build and run the application

```
docker-compose up --build
```

5. Open your browser and go to `http://localhost:8080`

## Prerequisites

At least one of the following API keys:
- [OpenAI API key](https://platform.openai.com/docs/quickstart)
- [Anthropic API key](https://console.anthropic.com/)

Note: You can use any combination of the API keys above, but at least one is required to use the app.

Additional prerequisites for local deployment:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Supported models

### OpenAI

* GPT-5.6 Sol
* GPT-5.6 Luna

### Anthropic

* Claude Opus 5
* Claude Sonnet 5

## Core features

**Create** - Generate BPMN diagrams from plain-language descriptions, including pools, lanes, and message flows.

**Edit** - Modify processes conversationally or import BPMN files with drag and drop.

**Understand** - Ask questions about existing diagrams or use images to create and modify processes.

## Supported elements

The application currently supports a subset of BPMN elements, including pools, lanes, and message flows:

### Tasks
* Task
* User task
* Service task
* Send task
* Receive task
* Business rule task
* Manual task
* Script task

Tasks also support loop and sequential/parallel multi-instance markers.

### Gateways
* Exclusive gateway
* Parallel gateway
* Inclusive gateway

### Events
**Start events**
* Start event
* Timer start event
* Message start event
* Signal and conditional start events

**End events**
* End event
* Message end event
* Signal, error, escalation, terminate, and compensation end events

**Intermediate events**
* Intermediate throw event (generic)
* Intermediate throw event (message)
* Intermediate catch event (generic)
* Intermediate catch event (timer)
* Intermediate catch event (message)
* Signal and link intermediate events (throw/catch)
* Escalation and compensation intermediate throw events
* Conditional intermediate catch event

Text annotations and their associations are also supported.

## Limitations

* The AI assistant does not "see" manual edits made to the diagram. It always responds based on its last generated
  version. Keep this in mind when interacting with the assistant after making manual changes.
* Nested lanes are not supported yet.
* Each non-empty pool must contain exactly one start event.

## Paper

[BPMN Assistant: An LLM-Based Approach to Business Process Modeling](https://doi.org/10.3390/app16052213)

## Contact

If you have any questions or feedback, please open an issue on this GitHub repository or [contact me](https://jtlicardo.com/).
