import json
import threading
import tomllib
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"


class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    model_path: str = Field(
        "/models/llama-jb.gguf", description="Path to the model file"
    )
    max_tokens: int = Field(
        2048, description="Maximum number of tokens per request"
    )  # Updated from 4096 to 2048
    max_input_tokens: Optional[int] = Field(
        None,
        description="Maximum input tokens to use across all requests (None for unlimited)",
    )
    temperature: float = Field(0.0, description="Sampling temperature")

    # Optional vision model settings
    vision: Optional["LLMSettings"] = Field(None, description="Vision model settings")


class ProxySettings(BaseModel):
    server: str = Field(None, description="Proxy server address")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")


class SearchSettings(BaseModel):
    engine: str = Field(default="Google", description="Search engine the llm to use")
    fallback_engines: List[str] = Field(
        default_factory=lambda: ["DuckDuckGo", "Baidu", "Bing"],
        description="Fallback search engines to try if the primary engine fails",
    )
    retry_delay: int = Field(
        default=60,
        description="Seconds to wait before retrying all engines again after they all fail",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of times to retry all engines when all fail",
    )
    lang: str = Field(default="en", description="Language code for search results")
    country: str = Field(default="us", description="Country code for search results")


class BrowserSettings(BaseModel):
    headless: bool = Field(
        default=False, description="Whether to run browser in headless mode"
    )
    disable_security: bool = Field(
        default=True, description="Disable browser security features"
    )
    window_width: int = Field(default=642, description="Browser window width in pixels")
    window_height: int = Field(
        default=642, description="Browser window height in pixels"
    )
    extra_chromium_args: List[str] = Field(
        default_factory=list, description="Extra arguments to pass to the browser"
    )
    chrome_instance_path: Optional[str] = Field(
        None, description="Path to a Chrome instance to use"
    )
    wss_url: Optional[str] = Field(
        None, description="Connect to a browser instance via WebSocket"
    )
    cdp_url: Optional[str] = Field(
        None, description="Connect to a browser instance via CDP"
    )
    proxy: Optional[ProxySettings] = Field(None, description="Proxy settings")


class SandboxSettings(BaseModel):
    use_sandbox: bool = Field(default=False, description="Whether to use sandbox")
    image: str = Field(default="python:3.12-slim", description="Docker image to use")
    work_dir: str = Field(
        default="/workspace", description="Working directory in container"
    )
    memory_limit: str = Field(default="1g", description="Memory limit for container")
    cpu_limit: float = Field(default=2.0, description="CPU limit for container")
    timeout: int = Field(default=300, description="Timeout in seconds")
    network_enabled: bool = Field(default=True, description="Whether to enable network")


class MCPServerConfig(BaseModel):
    type: str = Field(default="sse", description="Server type (sse or stdio)")
    url: Optional[str] = Field(None, description="Server URL for SSE connections")
    command: Optional[str] = Field(None, description="Command for stdio connections")
    args: List[str] = Field(
        default_factory=list, description="Arguments for stdio command"
    )


class MCPConfig(BaseModel):
    server_reference: str = Field(
        default="app.mcp.server", description="MCP server module reference"
    )
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="MCP server configurations"
    )


class AgentRouterSettings(BaseModel):
    """Configuration for agent routing system."""

    enabled: bool = Field(default=True, description="Whether agent routing is enabled")
    default_agent: str = Field(default="manus", description="Default agent to use")


class MemorySettings(BaseModel):
    """Configuration for memory system."""

    save_session: bool = Field(default=False, description="Whether to save sessions")
    recover_last_session: bool = Field(
        default=False, description="Whether to recover last session"
    )
    memory_compression: bool = Field(
        default=False, description="Whether to compress memory"
    )


class VoiceSettings(BaseModel):
    """Configuration for voice interaction."""

    speak: bool = Field(default=False, description="Whether to enable text-to-speech")
    listen: bool = Field(default=False, description="Whether to enable speech-to-text")
    agent_name: str = Field(
        default="Friday", description="Agent name for voice interaction"
    )


class GPUSettings(BaseModel):
    """Configuration for GPU optimization."""

    force_cuda: bool = Field(
        default=True, description="Force CUDA usage for better performance"
    )
    force_gpu_layers: int = Field(
        default=0, description="Number of GPU layers to force"
    )
    memory_threshold: float = Field(
        default=0.8, description="Warning threshold for GPU memory usage"
    )
    cleanup_threshold: float = Field(
        default=0.9, description="Automatic cleanup threshold for GPU memory"
    )
    auto_cleanup: bool = Field(
        default=True, description="Enable automatic memory cleanup"
    )
    fallback_to_cpu: bool = Field(
        default=True, description="Fallback to CPU when GPU memory insufficient"
    )
    enable_monitoring: bool = Field(
        default=True, description="Enable background memory monitoring"
    )
    monitoring_interval: float = Field(
        default=300.0, description="Monitoring interval in seconds"
    )
    text_model_priority: str = Field(
        default="high", description="Priority for text model GPU allocation"
    )
    vision_model_priority: str = Field(
        default="medium", description="Priority for vision model GPU allocation"
    )
    max_gpu_layers_text: int = Field(
        default=-1, description="Max GPU layers for text model"
    )
    max_gpu_layers_vision: int = Field(
        default=-1, description="Max GPU layers for vision model"
    )
    enable_quantization: bool = Field(
        default=False, description="Enable model quantization"
    )
    mixed_precision: bool = Field(
        default=True, description="Enable FP16 inference for memory savings"
    )
    context_optimization: bool = Field(
        default=True, description="Enable adaptive context sizing"
    )
    batch_optimization: bool = Field(
        default=True, description="Enable batch processing optimization"
    )


class CUDASettings(BaseModel):
    """Configuration for CUDA-specific settings."""

    memory_fraction: float = Field(
        default=0.8, description="Reserve fraction of GPU memory for models"
    )
    enable_memory_pool: bool = Field(
        default=True, description="Enable CUDA memory pooling"
    )
    synchronize_operations: bool = Field(
        default=True, description="Synchronize CUDA operations for stability"
    )
    stream_optimization: bool = Field(
        default=True, description="Enable CUDA stream optimization"
    )


class ModelsSettings(BaseModel):
    """Configuration for model loading optimization."""

    lazy_loading: bool = Field(
        default=False, description="Enable lazy loading of models"
    )
    cache_models: bool = Field(default=True, description="Keep models in memory")
    unload_unused: bool = Field(
        default=False, description="Unload unused models to free memory"
    )


class Config(BaseModel):
    llm: LLMSettings
    browser: Optional[BrowserSettings] = None
    search: Optional[SearchSettings] = None
    sandbox: Optional[SandboxSettings] = None
    mcp_config: MCPConfig = Field(default_factory=MCPConfig)
    workspace_root: str = Field(
        default=str(WORKSPACE_ROOT), description="Workspace root directory"
    )
    agent_router: Optional[AgentRouterSettings] = Field(
        default_factory=AgentRouterSettings
    )
    memory: Optional[MemorySettings] = Field(default_factory=MemorySettings)
    voice: Optional[VoiceSettings] = Field(default_factory=VoiceSettings)
    gpu: Optional[GPUSettings] = Field(default_factory=GPUSettings)
    cuda: Optional[CUDASettings] = Field(default_factory=CUDASettings)
    models: Optional[ModelsSettings] = Field(default_factory=ModelsSettings)


# Thread-local storage for config
_thread_local = threading.local()


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a TOML file.
    Args:
        config_path: Path to the configuration file
    Returns:
        Config object
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "config.toml"

    # Initialize MCP config outside try block to ensure it's always available
    mcp_config = MCPConfig(server_reference="app.mcp.server")

    try:
        with open(config_path, "rb") as f:
            config_dict = tomllib.load(f)

        # Convert llm section to LLMSettings if it's a dict
        if "llm" in config_dict and isinstance(config_dict["llm"], dict):
            llm_dict = config_dict["llm"]

            # Handle vision settings if present
            if "vision" in llm_dict and isinstance(llm_dict["vision"], dict):
                vision_settings = LLMSettings(**llm_dict["vision"])
                llm_dict["vision"] = vision_settings

            # Create LLMSettings instance
            config_dict["llm"] = LLMSettings(**llm_dict)

        # Handle MCP configuration
        if "mcp" in config_dict:
            if isinstance(config_dict["mcp"], dict):
                if "server_reference" in config_dict["mcp"]:
                    mcp_config.server_reference = config_dict["mcp"]["server_reference"]

                # Process servers if present
                if "servers" in config_dict["mcp"] and isinstance(
                    config_dict["mcp"]["servers"], dict
                ):
                    for server_id, server_data in config_dict["mcp"]["servers"].items():
                        mcp_config.servers[server_id] = MCPServerConfig(**server_data)

        config_dict["mcp_config"] = mcp_config

        # Ensure workspace_root is set
        if "workspace_root" not in config_dict:
            config_dict["workspace_root"] = str(WORKSPACE_ROOT)

        return Config(**config_dict)
    except Exception as e:
        # If config file doesn't exist or is invalid, create a default config
        print(f"Error loading config: {e}")
        print("Using default configuration")

        # Default configuration for local GGUF models
        vision_settings = LLMSettings(
            model="qwen-vl-7b",
            model_path="/models/qwen-vl-7b-awq.gguf",
            max_tokens=2048,  # Updated from 4096 to 2048
            temperature=0.0,
        )

        llm_settings = LLMSettings(
            model="llama-jb",
            model_path="/models/llama-jb.gguf",
            max_tokens=2048,  # Updated from 4096 to 2048
            temperature=0.0,
            vision=vision_settings,
        )

        default_config = Config(
            llm=llm_settings, workspace_root=str(WORKSPACE_ROOT), mcp_config=mcp_config
        )

        return default_config


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the configuration for the current thread.
    Args:
        config_path: Optional path to configuration file
    Returns:
        Config object
    """
    # If a specific config path is provided, always load it fresh
    if config_path:
        return load_config(config_path)

    # Otherwise use thread-local caching
    if not hasattr(_thread_local, "config"):
        _thread_local.config = load_config()
    return _thread_local.config


# Global config instance
config = get_config()
