# Orion - Personal Cognitive Augmentation Assistant

A privacy-first AI assistant with persistent memory and context awareness.

## Features

- 🧠 **Persistent Memory** - Vector database for semantic search through past conversations
- 🔒 **Privacy-First** - Runs locally with Ollama, your data stays on your machine
- 📚 **Vault Integration** - Reads from your personal knowledge vault (Obsidian compatible)
- 💬 **Telegram Interface** - Chat through Telegram with rich formatting
- 🎯 **Context-Aware** - Automatically retrieves relevant past context and notes
- ✨ **Enhanced Responses** - Uncertainty markers, source citations, and conflict detection

## Setup

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd orion_v0
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and add your tokens:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/botfather)

### 3. Configure Application

Copy the example config and customize:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml`:
- Set `storage.vault.path` to your personal vault directory (or use the default `vault/`)
- Adjust LLM settings if needed

### 4. Set Up Ollama

Install and start Ollama:

```bash
# Install Ollama from https://ollama.ai
# Then pull your preferred model
ollama pull gemma3:12b  # or llama3.2, mistral, etc.
ollama serve
```

### 5. Create Vault Structure (Optional)

If you don't have an existing Obsidian vault:

```bash
mkdir -p vault/_SYSTEM
mkdir -p vault/projects
```

Create your identity file at `vault/_SYSTEM/core-identity.md` (see `vault/_SYSTEM/core-identity.md.example`)

### 6. Run

```bash
python main.py
```

## Data Privacy

⚠️ **IMPORTANT**: This repository is configured to keep your personal data private:

- ✅ `data/` - All conversation memory and vector DB (excluded from git)
- ✅ `vault/` - Your personal knowledge base (excluded from git)
- ✅ `.env` - Your secrets and tokens (excluded from git)
- ✅ `config.yaml` - Your personal config (excluded from git)

Use the `.example` files as templates to set up your personal configuration.

## Architecture

```
orion_v0/
├── main.py              # Entry point
├── config.yaml          # Your config (not in git)
├── .env                 # Your secrets (not in git)
├── data/                # Memory storage (not in git)
│   ├── vector_db/       # Conversation embeddings
│   └── buffer/          # Recent conversation buffer
├── vault/               # Your knowledge base (not in git)
│   ├── _SYSTEM/         # Core identity
│   └── projects/        # Project notes
└── src/
    ├── core/            # Core processing logic
    ├── llm/             # LLM client (Ollama)
    ├── plugins/         # Storage & retrieval plugins
    └── interfaces/      # Telegram bot interface
```

## Plugins

### Storage Plugins
- **VectorDBPlugin** - Stores message embeddings for semantic search
- **ConversationBufferPlugin** - Maintains recent conversation history

### Retrieval Plugins
- **CoreIdentityPlugin** - Loads your personal preferences/identity
- **VaultReaderPlugin** - Searches your knowledge vault
- **VectorSearchPlugin** - Semantic search through past conversations

## Requirements

- Python 3.9+
- Ollama running locally
- Telegram Bot Token

## License

MIT License - See LICENSE file for details
