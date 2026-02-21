import gradio as gr  # 导入gradio库用于创建GUI

from config import Config  # 导入配置管理模块
from github_client import GitHubClient  # 导入用于GitHub API操作的客户端
from hacker_news_client import HackerNewsClient  # 导入用于Hacker News操作的客户端
from report_generator import ReportGenerator  # 导入报告生成器模块
from llm import LLM  # 导入可能用于处理语言模型的LLM类
from subscription_manager import SubscriptionManager  # 导入订阅管理器
from logger import LOG  # 导入日志记录器

# 创建各个组件的实例
config = Config()
github_client = GitHubClient(config.github_token)
hacker_news_client = HackerNewsClient()
llm = LLM(config)
report_generator = ReportGenerator(llm)
subscription_manager = SubscriptionManager(config.subscriptions_file)

def export_progress_by_date_range(repo, days):
    # 定义一个函数，用于导出和生成指定时间范围内项目的进展报告
    raw_file_path = github_client.export_progress_by_date_range(repo, days)  # 导出原始数据文件路径
    report, report_file_path = report_generator.generate_report_by_date_range(raw_file_path, days)  # 生成并获取报告内容及文件路径

    return report, report_file_path  # 返回报告内容和报告文件路径

def generate_hacker_news_report():
    # 定义一个函数，用于生成 Hacker News 趋势报告
    raw_file_path = hacker_news_client.export_top_stories()  # 导出 Hacker News 热门话题
    report, report_file_path = report_generator.generate_hacker_news_report(raw_file_path)  # 生成并获取报告内容及文件路径

    return report, report_file_path  # 返回报告内容和报告文件路径

# 创建Gradio界面
with gr.Blocks(title="GitHubSentinel") as demo:
    gr.Markdown("# GitHubSentinel")
    gr.Markdown("## 智能信息检索和高价值内容挖掘工具")
    
    # 创建标签页
    with gr.Tab("GitHub 项目进展"):
        gr.Markdown("### GitHub 项目进展报告")
        
        # 创建输入组件
        repo_input = gr.Dropdown(
            subscription_manager.list_subscriptions(), label="订阅列表", info="已订阅GitHub项目"
        )
        days_input = gr.Slider(value=2, minimum=1, maximum=7, step=1, label="报告周期", info="生成项目过去一段时间进展，单位：天")
        
        # 创建按钮
        github_button = gr.Button("生成报告")
        
        # 设置输出组件
        github_markdown = gr.Markdown()
        github_file = gr.File(label="下载报告")
        
        # 绑定按钮点击事件
        github_button.click(export_progress_by_date_range, inputs=[repo_input, days_input], outputs=[github_markdown, github_file])
    
    with gr.Tab("Hacker News 趋势"):
        gr.Markdown("### Hacker News 趋势报告")
        
        # 创建按钮
        hn_button = gr.Button("生成趋势报告")
        
        # 设置输出组件
        hn_markdown = gr.Markdown()
        hn_file = gr.File(label="下载报告")
        
        # 绑定按钮点击事件
        hn_button.click(generate_hacker_news_report, inputs=[], outputs=[hn_markdown, hn_file])

if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0")  # 启动界面并设置为公共可访问
    # 可选带有用户认证的启动方式
    # demo.launch(share=True, server_name="0.0.0.0", auth=('django', '1234'))