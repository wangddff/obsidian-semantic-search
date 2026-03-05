# Obsidian Semantic Search with BGE-M3 and LanceDB

[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-90%25%20complete-yellow)]()

A powerful semantic search system for Obsidian notes using BGE-M3 embeddings and LanceDB vector database.

## 🚀 Features

- **BGE-M3 Integration**: State-of-the-art Chinese-optimized embeddings via LM Studio API
- **Smart Chunking**: Intelligent text segmentation (2000-4000 characters with overlap)
- **LanceDB Vector Store**: Efficient 1024-dimensional vector storage and retrieval
- **Obsidian Support**: Full support for Markdown, frontmatter, and Obsidian-specific formats
- **Semantic Search**: Natural language queries with cosine similarity ranking
- **API-Based Architecture**: Flexible model deployment via HTTP API

## 📋 Prerequisites

- Python 3.14+
- [LM Studio](https://lmstudio.ai/) running BGE-M3 model
- Network access to LM Studio API (default: `http://192.168.1.4:1234`)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/obsidian-semantic-search.git
   cd obsidian-semantic-search
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure LM Studio**
   - Start LM Studio
   - Load BGE-M3 model
   - Enable API server on port 1234
   - Update `config/config.yaml` if needed

## ⚙️ Configuration

Edit `config/config.yaml`:

```yaml
model:
  api:
    base_url: "http://192.168.1.4:1234"  # LM Studio API endpoint
    model_name: "text-embedding-bge-m3"  # BGE-M3 model name
    timeout: 30
    max_retries: 3

text_processing:
  chunk_size: 3000      # Target chunk size in characters
  chunk_overlap: 300    # Overlap between chunks
  min_chunk_size: 2000  # Minimum chunk size
  max_chunk_size: 4000  # Maximum chunk size
  adaptive_chunking: true

lancedb:
  table_name: "obsidian_embeddings_bge_m3"
  vector_dimension: 1024  # BGE-M3 vector dimension
  metric_type: "cosine"
```

## 🚀 Quick Start

### 1. Test API Connectivity
```bash
python quick_verify.py
```

### 2. Process Your Obsidian Vault
```python
from src.pipeline_integration import ObsidianSemanticSearchPipeline

# Initialize pipeline
pipeline = ObsidianSemanticSearchPipeline("./config/config.yaml")
pipeline.initialize_components()

# Process your Obsidian vault
stats = pipeline.process_directory("/path/to/your/obsidian/vault")
print(f"Processed {stats.total_files} files, created {stats.total_chunks} chunks")

# Search for content
results = pipeline.search("machine learning techniques", limit=5)
for result in results:
    print(f"Score: {result.score:.3f} | File: {result.metadata['file_path']}")
    print(f"Text: {result.text[:200]}...\n")
```

### 3. Command Line Interface
```bash
# Process directory
python -m src.pipeline_integration --config config/config.yaml --input /path/to/vault

# Search interactively
python -m src.pipeline_integration --search "your query" --limit 10
```

## 📁 Project Structure

```
obsidian_semantic_search/
├── src/                          # Source code
│   ├── bge_m3_client.py         # BGE-M3 API client
│   ├── text_extractor.py        # Markdown text extraction
│   ├── chunk_processor.py       # Intelligent text chunking
│   ├── embedding_generator.py   # BGE-M3 embedding generation
│   ├── vector_store.py          # LanceDB vector operations
│   └── pipeline_integration.py  # Complete pipeline
├── config/                       # Configuration files
│   └── config.yaml              # Main configuration
├── tests/                        # Test files
├── data/                         # Data directory
│   └── test_results/            # Test results
├── requirements.txt              # Python dependencies
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🔧 Core Components

### 1. BGE-M3 Client (`src/bge_m3_client.py`)
- HTTP API wrapper for LM Studio BGE-M3 model
- Batch processing with error handling and retries
- Concurrent requests for improved performance

### 2. Text Extractor (`src/text_extractor.py`)
- Extracts plain text from Markdown files
- Preserves frontmatter metadata
- Handles Obsidian-specific formats and links

### 3. Chunk Processor (`src/chunk_processor.py`)
- Intelligent text segmentation (2000-4000 characters)
- Overlap strategy for context preservation
- Adaptive chunking based on content structure

### 4. Embedding Generator (`src/embedding_generator.py`)
- Integrates with BGE-M3 client
- Batch embedding generation
- Vector normalization for similarity calculation

### 5. Vector Store (`src/vector_store.py`)
- LanceDB integration for vector storage
- 1024-dimensional vector support
- Efficient similarity search with filtering

### 6. Pipeline Integration (`src/pipeline_integration.py`)
- End-to-end processing pipeline
- Configuration management
- Performance monitoring and reporting

## 🧪 Testing

Run the test suite:

```bash
# Test environment
python test_environment.py

# Test BGE-M3 integration
python test_bge_m3_integration.py

# Test full pipeline
python test_full_pipeline.py

# Test vector operations
python test_vector_basic.py
```

## 📊 Performance

- **API Response Time**: ~50-200ms per request
- **Chunk Processing**: 0.02 seconds for 10 files (30 chunks)
- **Vector Search**: <100ms response time
- **Memory Usage**: Optimized for 1.5GB+ note collections

## 🔍 Search Examples

```python
# Technical topics
results = pipeline.search("Python async programming patterns", limit=5)

# Personal notes
results = pipeline.search("meeting notes from last week about project X", limit=3)

# Cross-referencing
results = pipeline.search("connections between machine learning and neuroscience", limit=10)
```

## 🖥️ Command Line Interface

The project includes a CLI tool for easy interaction:

### Basic Usage

```bash
# Test system connectivity
python cli.py test

# Process an Obsidian vault directory
python cli.py process /path/to/your/obsidian/vault

# Perform semantic search
python cli.py search "machine learning techniques" --limit 5

# Show database statistics
python cli.py stats

# Get help
python cli.py --help
```

### Advanced Examples

```bash
# Process directory with custom config
python cli.py --config ./config/custom.yaml process /path/to/vault

# Search with verbose output
python cli.py search "artificial intelligence" -l 10 -v

# Test specific components
python cli.py test
```

### Docker Usage

```bash
# Build the Docker image
docker build -t obsidian-semantic-search .

# Run with Docker Compose
docker-compose up -d

# Run CLI commands inside container
docker run -v ./data:/app/data -v ./config:/app/config obsidian-semantic-search test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding) by FlagOpen
- [LanceDB](https://lancedb.github.io/lancedb/) for vector storage
- [LM Studio](https://lmstudio.ai/) for local model serving
- [Obsidian](https://obsidian.md/) for the amazing note-taking experience

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/obsidian-semantic-search/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/obsidian-semantic-search/discussions)
- **Email**: your.email@example.com

## 📈 Roadmap

- [x] Basic text extraction and chunking
- [x] BGE-M3 model integration
- [x] LanceDB vector storage
- [x] Semantic search functionality
- [ ] Web interface
- [ ] Real-time indexing
- [ ] Multi-language support
- [ ] Plugin for Obsidian

---

**Made with ❤️ for the Obsidian community**

*If you find this project useful, please give it a ⭐ on GitHub!*
## 📝 更新日志

### [2026-03-05] v1.2.0 - Chunking策略优化
**重大性能提升**：
- ✅ **数据库大小减少61%**：从24MB优化到9.4MB
- ✅ **记录数减少62.8%**：从4316条减少到1607条
- ✅ **文件覆盖率100%**：小文件不再被过滤
- ✅ **搜索性能提升**：响应时间<0.05秒

**技术改进**：
1. **配置优化**：
   - `min_chunk_size`: 2000 → 10（处理所有小文件）
   - `chunk_size`: 3000 → 3800（充分利用BGE-M3容量）
   - `max_chunk_size`: 4000 → 4200（模型安全限制内）

2. **算法改进**：
   - 新增 `_split_very_long_sentence()` 方法
   - 多级分割：段落 → 句子 → 标点 → 固定大小
   - 确保超长文本正确分割

3. **质量提升**：
   - 更大分块提供更好的上下文理解
   - 避免过度分割导致的碎片化
   - 保持语义完整性同时减少存储

**实际效果**：
- 搜索"量化交易"：0.032秒返回结果
- 搜索"国金证券 账号"：0.038秒找到小文件（252字符）
- 平均分块/文件：3.1 → 1.15（减少过度分割）

### [2026-03-04] v1.1.0 - BGE-M3集成完成
- 集成BGE-M3模型通过LM Studio API
- 实现完整的语义搜索管道
- 添加CLI命令行工具
- 支持Obsidian笔记库别名

### [2026-03-03] v1.0.0 - 初始版本
- 基础文本提取和分块功能
- LanceDB向量存储集成
- 基本搜索功能实现
