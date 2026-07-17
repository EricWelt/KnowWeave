"""KnowWeave 后端配置：所有可调参数集中于此，均可通过 .env 覆盖。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ============ LLM Provider ============
# 可选值: "modelscope" | "moonshot"（通过 .env 中 LLM_PROVIDER 切换）
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "modelscope")

# --- Moonshot / Kimi ---
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
MOONSHOT_BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")

# --- ModelScope / Qwen ---
MODELSCOPE_API_KEY = os.getenv("MODELSCOPE_API_KEY") or os.getenv("LLM_API_KEY", "")
MODELSCOPE_BASE_URL = os.getenv(
    "MODELSCOPE_BASE_URL", "https://api-inference.modelscope.cn/v1/"
)
MODELSCOPE_MODEL = os.getenv("MODELSCOPE_MODEL", "Qwen/Qwen3-32B")


# ============ LLM 模型注册表（推荐用法） ============
# 通过 LLM_MODEL=<名称> 选择模型，切换只需改 .env 一行，无需改代码。
# 每项字段：
#   api_key_env   API key 所在环境变量名
#   base_url      OpenAI 兼容端点
#   model         模型 ID（OpenAI SDK 的 model 参数）
#   min_interval  该模型的最小调用间隔秒数（0 = 不限速；账户 RPM 低时调大）
LLM_MODELS = {
    # ---- Kimi / Moonshot ----
    "moonshot-128k": {
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-128k",
        "min_interval": 21,
    },
    "moonshot-32k": {
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-32k",
        "min_interval": 21,
    },
    "kimi-k2": {
        "api_key_env": "MOONSHOT_API_KEY",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k2-0711-preview",
        "min_interval": 21,
    },
    # ---- ModelScope / Qwen（免费额度） ----
    # 已验证可用的模型（首次冒烟即用它跑通）
    "qwen3-coder-30b": {
        "api_key_env": "MODELSCOPE_API_KEY",
        "base_url": "https://api-inference.modelscope.cn/v1/",
        "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "min_interval": 1.0,
    },
    "qwen3-32b": {
        "api_key_env": "MODELSCOPE_API_KEY",
        "base_url": "https://api-inference.modelscope.cn/v1/",
        "model": "Qwen/Qwen3-32B",
        "min_interval": 1.0,
    },
    # ---- NVIDIA build ----
    # GLM-5.2（智谱，当前默认；实测可用）
    # 注意：ReAct 会话会连发多次调用，必须限速防止击穿 40 RPM 预算
    "glm-5.2": {
        "api_key_env": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "z-ai/glm-5.2",
        "min_interval": 3.0,  # 20 RPM，留 50% 余量
    },
    # MiniMax M3（1M 上下文；曾 429 模型级配额，配额恢复后可切回）
    "minimax-m3": {
        "api_key_env": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "minimaxai/minimax-m3",
        "min_interval": 2.0,
    },
    # NVIDIA 自家 Llama 系旗舰（实测可用）
    "nemotron-49b": {
        "api_key_env": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia/llama-3.3-nemotron-super-49b-v1",
        "min_interval": 3.0,
    },
}

# 当前使用的模型（按需切换：qwen3-coder-30b / glm-5.2 / moonshot-128k ...）
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3-coder-30b")

# ============ Agent 引擎参数 ============
MAX_STEPS = int(os.getenv("MAX_STEPS", "15"))                 # 防无限循环
TOOL_OUTPUT_MAX_CHARS = int(os.getenv("TOOL_OUTPUT_MAX_CHARS", "2000"))  # 工具输出截断
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))  # 推理稳定性
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "300"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "60"))           # 单次 LLM 调用超时
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))
# 全局最小调用间隔覆盖（秒）：0 = 按模型注册表的 min_interval；
# 若 >0 则强制覆盖所有模型（如想临时把某个模型间隔调大/调小）
LLM_MIN_INTERVAL = float(os.getenv("LLM_MIN_INTERVAL", "0"))
MEMORY_RECENT_TURNS = int(os.getenv("MEMORY_RECENT_TURNS", "10"))  # 短期记忆轮数

# ============ 存储 ============
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "knowweave.sqlite"))
CHROMA_PATH = os.getenv("CHROMA_PATH", str(DATA_DIR / "chroma_db"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "note_chunks")

# ============ JWT ============
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", str(7 * 24 * 60)))  # 7 天

# ============ Embedding / RAG ============
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "512"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# ============ 文件上传 ============
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".pptx", ".md"}
UPLOAD_TEMP_DIR = DATA_DIR / "uploads"