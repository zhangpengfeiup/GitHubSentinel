import os
import json
import requests
from openai import OpenAI  # 导入OpenAI库用于访问GPT模型
from logger import LOG  # 导入日志模块

class LLM:
    def __init__(self, config):
        self.config = config
        self.model_type = config.llm_model_type.lower()
        
        # 从TXT文件加载提示信息
        with open("prompts/report_prompt.txt", "r", encoding='utf-8') as file:
            self.system_prompt = file.read()
        
        # 加载 Hacker News 提示信息
        try:
            with open("prompts/hacker_news_prompt.txt", "r", encoding='utf-8') as file:
                self.hacker_news_prompt = file.read()
        except FileNotFoundError:
            LOG.warning("Hacker News 提示文件未找到，使用默认提示")
            self.hacker_news_prompt = "你是一名专业的技术分析助手，请分析以下 Hacker News 热门话题，总结出主要趋势和热点领域。"
        
        # 初始化模型客户端
        if self.model_type == "openai":
            # 创建一个OpenAI客户端实例
            self.client = OpenAI()
        elif self.model_type == "ollama":
            # Ollama 不需要提前创建客户端，使用 API 调用
            pass
        else:
            LOG.error(f"不支持的模型类型: {self.model_type}")
            raise ValueError(f"不支持的模型类型: {self.model_type}")

    def generate_daily_report(self, markdown_content, dry_run=False):
        # 使用从TXT文件加载的提示信息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": markdown_content},
        ]

        if dry_run:
            # 如果启用了dry_run模式，将不会调用模型，而是将提示信息保存到文件中
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/prompt.txt", "w+") as f:
                # 格式化JSON字符串的保存
                json.dump(messages, f, indent=4, ensure_ascii=False)
            LOG.debug("Prompt已保存到 daily_progress/prompt.txt")

            return "DRY RUN"

        # 调用模型生成报告
        return self._generate_report(messages, "GitHub 项目报告")
    
    def generate_hacker_news_report(self, markdown_content, dry_run=False):
        # 使用 Hacker News 提示信息
        messages = [
            {"role": "system", "content": self.hacker_news_prompt},
            {"role": "user", "content": markdown_content},
        ]

        if dry_run:
            # 如果启用了dry_run模式，将不会调用模型，而是将提示信息保存到文件中
            LOG.info("Dry run mode enabled. Saving prompt to file.")
            with open("daily_progress/hacker_news_prompt.txt", "w+") as f:
                # 格式化JSON字符串的保存
                json.dump(messages, f, indent=4, ensure_ascii=False)
            LOG.debug("Prompt已保存到 daily_progress/hacker_news_prompt.txt")

            return "DRY RUN"

        # 调用模型生成报告
        return self._generate_report(messages, "Hacker News 趋势报告")
    
    def _generate_report(self, messages, report_type):
        # 日志记录开始生成报告
        if self.model_type == "openai":
            LOG.info(f"使用 OpenAI {self.config.openai_model_name} 模型开始生成 {report_type}。")
        elif self.model_type == "ollama":
            LOG.info(f"使用 Ollama {self.config.ollama_model_name} 模型开始生成 {report_type}。")
        
        try:
            if self.model_type == "openai":
                # 调用OpenAI GPT模型生成报告
                response = self.client.chat.completions.create(
                    model=self.config.openai_model_name,  # 使用配置中的模型名称
                    messages=messages
                )
                LOG.debug("GPT response: {}", response)
                # 返回模型生成的内容
                return response.choices[0].message.content
            elif self.model_type == "ollama":
                # 调用 Ollama 模型生成报告
                payload = {
                    "model": self.config.ollama_model_name,
                    "messages": messages,
                    "stream": False
                }
                response = requests.post(
                    self.config.ollama_api_url,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                response_data = response.json()
                LOG.debug("Ollama response: {}", response_data)
                return response_data.get("message", {}).get("content", "")
        except Exception as e:
            # 如果在请求过程中出现异常，记录错误并抛出
            LOG.error(f"生成报告时发生错误：{e}")
            raise
