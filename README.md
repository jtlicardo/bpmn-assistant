# BPMN Assistant

BPMN Assistant is an application that uses Large Language Models (LLMs) to assist with creating, editing, and interpreting Business Process Model and Notation (BPMN) diagrams.

## Quickstart
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

- [Docker](https://docs.docker.com/get-docker/)  
- [Docker Compose](https://docs.docker.com/compose/install/)  
- [Anthropic API key](https://console.anthropic.com/) or [OpenAI API key](https://platform.openai.com/docs/quickstart) (preferably both)  

## Screenshots

![Screenshot](images/screenshot_1.png)

![Screenshot](images/screenshot_2.png)

## Core features

1. Diagram creation - Generates BPMN diagrams based on text descriptions.
2. Diagram editing - Modifies BPMN diagrams based on user input.
3. Diagram interpretation - Provides text descriptions of BPMN diagrams.

## Supported elements

The application currently supports a subset of BPMN elements:

### Tasks

* Regular task
* User task
* Service task

### Gateways

* Exclusive gateway
* Parallel gateway

### Events

* Start event
* End event

## Limitations

* The application currently only supports a subset of BPMN elements.
* The quality of the output depends on the underlying AI models and may not always be perfect.

## Contact

If you have any questions or feedback, please open an issue on this GitHub repository.