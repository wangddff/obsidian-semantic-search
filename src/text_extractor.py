#!/usr/bin/env python3
"""
文本提取模块
负责从Markdown文件中提取纯文本内容
"""

import os
import re
import frontmatter
from typing import Dict, List, Optional, Tuple
import markdown
from bs4 import BeautifulSoup


class TextExtractor:
    """文本提取器"""
    
    def __init__(self, encoding: str = "utf-8", **kwargs):
        self.encoding = encoding
        self.markdown_parser = markdown.Markdown()
        # 接受但不使用额外的关键字参数以保持向后兼容性
        
    def extract_from_file(self, file_path: str) -> Dict:
        """
        从单个文件中提取文本内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含文本内容和元数据的字典
        """
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # 解析frontmatter
            post = frontmatter.loads(content)
            metadata = post.metadata
            text_content = post.content
            
            # 提取纯文本（去除Markdown格式）
            plain_text = self._markdown_to_text(text_content)
            
            # 获取文件信息
            file_info = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': os.path.getsize(file_path),
                'modified_time': os.path.getmtime(file_path)
            }
            
            return {
                'metadata': metadata,
                'content': plain_text,
                'original_content': text_content,
                'file_info': file_info
            }
            
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return None
    
    def extract_from_directory(self, directory_path: str, 
                              extensions: List[str] = ['.md', '.markdown']) -> List[Dict]:
        """
        从目录中提取所有文件的文本内容
        
        Args:
            directory_path: 目录路径
            extensions: 支持的文件扩展名
            
        Returns:
            所有文件的文本内容列表
        """
        extracted_contents = []
        
        for root, dirs, files in os.walk(directory_path):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    content = self.extract_from_file(file_path)
                    if content:
                        extracted_contents.append(content)
        
        return extracted_contents
    
    def _markdown_to_text(self, markdown_text: str) -> str:
        """
        将Markdown转换为纯文本
        
        Args:
            markdown_text: Markdown文本
            
        Returns:
            纯文本
        """
        # 先处理代码块
        markdown_text = self._remove_code_blocks(markdown_text)
        
        # 使用markdown转换为HTML
        html = self.markdown_parser.convert(markdown_text)
        
        # 使用BeautifulSoup提取纯文本
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        # 清理多余的空格和换行
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 多个空行合并为一个
        text = re.sub(r'[ \t]+', ' ', text)  # 多个空格合并为一个
        text = text.strip()
        
        return text
    
    def _remove_code_blocks(self, text: str) -> str:
        """
        移除代码块（保留代码块内容）
        
        Args:
            text: 包含代码块的文本
            
        Returns:
            移除代码块标记的文本
        """
        # 移除 ```代码块```
        text = re.sub(r'```[\s\S]*?```', '', text)
        # 移除 `行内代码`
        text = re.sub(r'`([^`]+)`', r'\1', text)
        return text
    
    def _extract_headings(self, markdown_text: str) -> List[Dict]:
        """
        提取标题结构
        
        Args:
            markdown_text: Markdown文本
            
        Returns:
            标题列表，每个标题包含level和text
        """
        headings = []
        lines = markdown_text.split('\n')
        
        for line in lines:
            # 匹配#开头的标题
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    'level': level,
                    'text': text
                })
        
        return headings


if __name__ == "__main__":
    # 测试代码
    extractor = TextExtractor()
    
    # 测试单个文件
    test_file = "/tmp/obsidian_test_data/测试文件.md"
    if os.path.exists(test_file):
        result = extractor.extract_from_file(test_file)
        print("单个文件提取结果:")
        print(f"文件: {result['file_info']['file_name']}")
        print(f"内容: {result['content'][:100]}...")
        print(f"元数据: {result['metadata']}")
    
    # 测试目录
    test_dir = "/tmp/obsidian_test_data/"
    if os.path.exists(test_dir):
        results = extractor.extract_from_directory(test_dir)
        print(f"\n目录提取结果: 共{len(results)}个文件")
        for i, result in enumerate(results[:3]):  # 只显示前3个
            print(f"{i+1}. {result['file_info']['file_name']}: {result['content'][:50]}...")