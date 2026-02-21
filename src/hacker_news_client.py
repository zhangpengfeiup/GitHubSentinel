import requests
import os
from datetime import datetime
from logger import LOG

class HackerNewsClient:
    def __init__(self):
        self.base_url = "https://hacker-news.firebaseio.com/v0"
    
    def get_top_stories(self, limit=30):
        """
        获取 Hacker News 热门故事
        """
        try:
            # 获取热门故事 ID 列表
            response = requests.get(f"{self.base_url}/topstories.json", timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:limit]
            
            stories = []
            for story_id in story_ids:
                # 获取每个故事的详细信息
                story_response = requests.get(f"{self.base_url}/item/{story_id}.json", timeout=10)
                story_response.raise_for_status()
                story = story_response.json()
                
                # 只处理有标题和 URL 的故事
                if "title" in story and "url" in story:
                    stories.append({
                        "id": story.get("id"),
                        "title": story.get("title"),
                        "url": story.get("url"),
                        "score": story.get("score"),
                        "by": story.get("by"),
                        "time": story.get("time"),
                        "descendants": story.get("descendants", 0)  # 评论数
                    })
            
            LOG.info(f"成功获取 {len(stories)} 条 Hacker News 热门故事")
            return stories
        except Exception as e:
            LOG.error(f"获取 Hacker News 热门故事时发生错误：{e}")
            return []
    
    def export_top_stories(self):
        """
        导出热门故事到 Markdown 文件
        """
        stories = self.get_top_stories()
        
        # 创建存储目录
        export_dir = "hacker_news"
        os.makedirs(export_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(export_dir, f"top_stories_{timestamp}.md")
        
        # 生成 Markdown 内容
        markdown_content = f"# Hacker News 热门话题 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n\n"
        markdown_content += "## 热门故事\n\n"
        
        for i, story in enumerate(stories, 1):
            # 转换时间戳为可读格式
            story_time = datetime.fromtimestamp(story["time"]).strftime("%Y-%m-%d %H:%M:%S")
            markdown_content += f"### {i}. {story['title']}\n"
            markdown_content += f"- URL: {story['url']}\n"
            markdown_content += f"- 评分: {story['score']}\n"
            markdown_content += f"- 作者: {story['by']}\n"
            markdown_content += f"- 发布时间: {story_time}\n"
            markdown_content += f"- 评论数: {story['descendants']}\n\n"
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        LOG.info(f"Hacker News 热门话题已导出到 {file_path}")
        return file_path