import json
import time
import requests
from openai import OpenAI  # 导入OpenAI库用于访问GPT模型
from logger import LOG  # 导入日志模块

# 默认 System role 基础描述，用于提升报告质量与输出稳定性（身份、格式、约束）
DEFAULT_SYSTEM_ROLE_BASE = """你是一名专业的技术报告撰写助手。请严格遵守以下规则：
- 仅根据用户提供的原始内容进行归纳与分类，不要编造或添加未出现的信息。
- 输出必须为合法 Markdown，使用中文撰写。
- 若无法从内容中明确分类，可将条目归入「其他」并简要说明。
- 保持结构清晰、条目不重复。"""


class LLM:
    def __init__(self, config):
        """
        初始化 LLM 类，根据配置选择使用的模型（OpenAI 或 Ollama）。

        :param config: 配置对象，包含所有的模型配置参数。
        """
        self.config = config
        self.model = config.llm_model_type.lower()  # 获取模型类型并转换为小写
        self._temperature = getattr(config, 'llm_temperature', 0.3)
        self._max_retries = getattr(config, 'llm_max_retries', 2)
        self._timeout = getattr(config, 'llm_timeout_seconds', 120)
        base = getattr(config, 'llm_system_role_base', None)
        self._system_role_base = (base or "").strip() or DEFAULT_SYSTEM_ROLE_BASE
        if self.model == "openai":
            # 检查 API Key 是否设置
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                error_msg = (
                    "OpenAI API Key 未设置！\n"
                    "请设置环境变量: export OPENAI_API_KEY='your-api-key'\n"
                    "或添加到 ~/.zshrc: echo 'export OPENAI_API_KEY=\"sk-...\"' >> ~/.zshrc"
                )
                LOG.error(error_msg)
                raise ValueError(error_msg)
            self.client = OpenAI(api_key=api_key)  # 创建OpenAI客户端实例
        elif self.model == "ollama":
            self.api_url = config.ollama_api_url  # 设置Ollama API的URL
        else:
            LOG.error(f"不支持的模型类型: {self.model}")
            raise ValueError(f"不支持的模型类型: {self.model}")  # 如果模型类型不支持，抛出错误

    def _build_system_content(self, task_prompt):
        """将固定的 System role 与任务相关 prompt 组合，提升报告质量与稳定。"""
        if not (task_prompt or "").strip():
            return self._system_role_base
        return f"{self._system_role_base}\n\n---\n\n{task_prompt.strip()}"

    def generate_report(self, system_prompt, user_content):
        """
        生成报告，根据配置选择不同的模型来处理请求。
        使用 System role（基础角色 + 任务 prompt）提升报告质量与稳定性，并带重试与超时。

        :param system_prompt: 任务相关的系统提示信息（与基础 System role 组合）。
        :param user_content: 用户提供的内容，通常是Markdown格式的文本。
        :return: 生成的报告内容。
        """
        system_content = self._build_system_content(system_prompt)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content or ""},
        ]
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                if self.model == "openai":
                    return self._generate_report_openai(messages)
                elif self.model == "ollama":
                    return self._generate_report_ollama(messages)
                else:
                    raise ValueError(f"不支持的模型类型: {self.model}")
            except Exception as e:
                last_error = e
                LOG.warning(f"生成报告第 {attempt + 1}/{self._max_retries + 1} 次失败: {e}")
                if attempt < self._max_retries:
                    time.sleep(1.0 * (attempt + 1))
        LOG.error(f"生成报告在 {self._max_retries + 1} 次重试后仍失败")
        raise last_error

    def _generate_report_openai(self, messages):
        """
        使用 OpenAI GPT 模型生成报告。

        :param messages: 包含系统提示和用户内容的消息列表。
        :return: 生成的报告内容。
        """
        LOG.info(f"使用 OpenAI {self.config.openai_model_name} 模型生成报告。")
        response = self.client.chat.completions.create(
            model=self.config.openai_model_name,
            messages=messages,
            temperature=self._temperature,
        )
        LOG.debug("GPT 响应: {}", response)
        return response.choices[0].message.content

    def _generate_report_ollama(self, messages):
        """
        使用 Ollama LLaMA 模型生成报告。

        :param messages: 包含系统提示和用户内容的消息列表。
        :return: 生成的报告内容。
        """
        LOG.info(f"使用 Ollama {self.config.ollama_model_name} 模型生成报告。")
        payload = {
            "model": self.config.ollama_model_name,
            "messages": messages,
            "max_tokens": 4000,
            "temperature": self._temperature,
            "stream": False,
        }
        response = requests.post(
            self.api_url,
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()
        response_data = response.json()
        LOG.debug("Ollama 响应: {}", response_data)
        message_content = response_data.get("message", {}).get("content", None)
        if message_content:
            return message_content
        LOG.error("无法从响应中提取报告内容。")
        raise ValueError("Ollama API 返回的响应结构无效")

if __name__ == '__main__':
    from config import Config  # 导入配置管理类
    config = Config()
    llm = LLM(config)

    markdown_content="""
# Progress for langchain-ai/langchain (2024-08-20 to 2024-08-21)

## Issues Closed in the Last 1 Days
- partners/chroma: release 0.1.3 #25599
- docs: few-shot conceptual guide #25596
- docs: update examples in api ref #25589
"""

    # 示例：生成 GitHub 报告
    system_prompt = "Your specific system prompt for GitHub report generation"
    github_report = llm.generate_report(system_prompt, markdown_content)
    LOG.debug(github_report)
