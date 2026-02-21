# AI File Intelligence System

A local AI-powered file organization system with multi-LLM routing, drag-and-drop interface, semantic understanding, and long-term memory.

## Features

- **Multi-LLM Routing**: Support for DeepSeek, Doubao, Tongyi, Zhipu, Baichuan, Wenxin
- **Task-Based Auto-Selection**: Automatically routes tasks to the best model (classify, decision, summarize, codegen, chat)
- **Drag & Drop File Organization**: Drop files into interface and AI automatically classifies and moves them
- **Natural Language Commands**: "Organize my Downloads", "Find reinforcement learning papers"
- **Long-term Memory**: System learns from your decisions over time
- **Safe Developer Mode**: Read code, generate patches, never directly overwrites files
- **Real-time Monitoring**: Track token usage, costs, latency, and success rates
- **Futuristic UI**: Dark mode, glassmorphism, neon accents, live activity console

## Architecture

```
project_root/
├── app/
│   ├── core/          # Config, models, events
│   ├── gui/           # PySide6 interface with control panel
│   ├── agent/         # Planner, Executor, MemoryReader
│   ├── memory/        # Vector + rule memory
│   ├── tools/         # Tool registry
│   ├── llm/           # Multi-LLM router
│   │   ├── base_provider.py
│   │   ├── providers.py    # All Chinese LLM providers
│   │   └── router.py      # Task routing & fallback
│   ├── data/          # Chroma DB, rules
│   └── config/        # YAML configuration
├── config/
│   └── models.yaml    # Model routing config
└── main.py
```

## Task Routing

The system automatically routes different task types to optimal models:

| Task Type | Default Model | Description |
|-----------|---------------|-------------|
| classify | Doubao | Fast and cheap for file classification |
| decision | DeepSeek | Strong reasoning for complex decisions |
| summarize | Tongyi | Long context for document understanding |
| codegen | DeepSeek | Best coding capabilities |
| chat | Doubao | Balanced for general conversation |

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config/models.yaml` to set your API keys:

```yaml
api_keys:
  deepseek: "your-deepseek-api-key"
  doubao: "your-doubao-api-key"
  tongyi: "your-tongyi-api-key"
  zhipu: "your-zhipu-api-key"
  baichuan: "your-baichuan-api-key"
  wenxin: "your-wenxin-api-key"
```

You can also customize the model routing:

```yaml
models:
  classify: doubao
  decision: deepseek
  summarize: tongyi
  codegen: deepseek
  chat: doubao
```

## Usage

```bash
python main.py
```

### Using the Control Panel

The rightmost panel provides:
- **Model Routing Editor**: Change which model handles each task type
- **Live Activity Console**: Real-time log of all LLM requests with latency, tokens, and cost
- **Statistics Dashboard**: Total requests, cost, tokens, average latency, and success rate

### Single Provider Mode

The system works with just one provider configured. If only one API key is set, all tasks will route to that provider automatically.

## Safety Features

- Files can only be moved within allowed workspace
- System directories are protected
- Low confidence decisions require user confirmation
- Developer mode only generates patches, never overwrites
- Automatic fallback to other providers if one fails

## Tech Stack

- **GUI**: PySide6 (Qt for Python)
- **Vector DB**: Chroma (local)
- **Embeddings**: BGE-small / E5-small
- **LLM**: DeepSeek / Doubao / Tongyi / Zhipu / Baichuan / Wenxin
- **Architecture**: Event-driven, tool-based agent, async, multi-LLM routing

## Agent Behavior

The AI agent follows these rules:

1. **Intent Classification**: Maps user input to task type
2. **Tool Priority**: Uses tools when possible instead of LLM
3. **Memory Usage**: Queries user habits before making decisions
4. **Confidence Rule**: Asks for confirmation if confidence < 0.8
5. **Developer Mode**: Only generates patches, never overwrites directly

## Cost Tracking

Every LLM request is logged with:
- Timestamp and provider
- Task type and model used
- Latency in milliseconds
- Token count (prompt + completion)
- Estimated cost

View real-time statistics in the Control Panel.
