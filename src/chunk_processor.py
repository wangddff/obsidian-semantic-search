#!/usr/bin/env python3
"""
分块处理模块
负责将提取的文本进行智能分块
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TextChunk:
    """文本分块数据类"""
    text: str
    metadata: Dict
    chunk_id: str
    start_pos: int
    end_pos: int
    file_path: str
    file_name: str
    heading_context: List[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'text': self.text,
            'metadata': self.metadata,
            'chunk_id': self.chunk_id,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'heading_context': self.heading_context or []
        }


class ChunkProcessor:
    """分块处理器"""
    
    def __init__(self, 
                 chunk_size: int = 3000,
                 chunk_overlap: int = 300,
                 min_chunk_size: int = 2000,
                 max_chunk_size: int = 4000):
        """
        初始化分块处理器
        
        Args:
            chunk_size: 目标分块大小（字符数）
            chunk_overlap: 分块重叠大小（字符数）
            min_chunk_size: 最小分块大小
            max_chunk_size: 最大分块大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_text(self, text: str, metadata: Dict, file_info: Dict) -> List[TextChunk]:
        """
        将文本分块
        
        Args:
            text: 要分块的文本
            metadata: 文件元数据
            file_info: 文件信息
            
        Returns:
            文本分块列表
        """
        # 清理文本
        text = text.strip()
        if not text:
            return []
        
        # 如果文本非常短，直接作为一个分块（即使小于min_chunk_size）
        if len(text) <= self.max_chunk_size:
            # 对于小文件，我们仍然要处理它，即使小于min_chunk_size
            return [self._create_chunk(text, 0, metadata, file_info)]
        
        # 按段落分割
        paragraphs = self._split_by_paragraphs(text)
        
        # 构建分块
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            # 如果当前段落太长，需要进一步分割
            if para_length > self.max_chunk_size:
                # 先把当前块保存
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    # 即使小于min_chunk_size也保存（避免丢失内容）
                    chunks.append(self._create_chunk(
                        chunk_text, 
                        len(chunks),
                        metadata,
                        file_info
                    ))
                
                # 分割长段落
                sub_chunks = self._split_long_paragraph(para, metadata, file_info)
                chunks.extend(sub_chunks)
                
                # 重置当前块
                current_chunk = []
                current_length = 0
                continue
            
            # 如果添加当前段落会超过分块大小，保存当前块
            if current_length + para_length > self.chunk_size:
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    # 即使小于min_chunk_size也保存
                    chunks.append(self._create_chunk(
                        chunk_text, 
                        len(chunks),
                        metadata,
                        file_info
                    ))
                
                # 开始新块，包含重叠
                if chunks and self.chunk_overlap > 0:
                    # 从上一个块的末尾取重叠部分
                    last_chunk = chunks[-1].text
                    overlap_text = last_chunk[-self.chunk_overlap:] if len(last_chunk) > self.chunk_overlap else last_chunk
                    current_chunk = [overlap_text, para]
                    current_length = len(overlap_text) + para_length
                else:
                    current_chunk = [para]
                    current_length = para_length
            else:
                # 添加到当前块
                current_chunk.append(para)
                current_length += para_length
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            # 即使小于min_chunk_size也保存
            chunks.append(self._create_chunk(
                chunk_text, 
                len(chunks),
                metadata,
                file_info
            ))
        
        return chunks
    
    def _split_by_paragraphs(self, text: str) -> List[str]:
        """
        按段落分割文本
        
        Args:
            text: 文本内容
            
        Returns:
            段落列表
        """
        # 按空行分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        # 清理每个段落
        cleaned_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para:  # 跳过空段落
                # 合并段落内的换行
                para = re.sub(r'\s+', ' ', para)
                cleaned_paragraphs.append(para)
        
        return cleaned_paragraphs
    
    def _split_long_paragraph(self, paragraph: str, metadata: Dict, file_info: Dict) -> List[TextChunk]:
        """
        分割长段落
        
        Args:
            paragraph: 长段落文本
            metadata: 元数据
            file_info: 文件信息
            
        Returns:
            分块列表
        """
        chunks = []
        
        # 按句子分割
        sentences = self._split_by_sentences(paragraph)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sent_length = len(sentence)
            
            # 如果单个句子就超过max_chunk_size，需要进一步分割
            if sent_length > self.max_chunk_size:
                # 先把当前块保存
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(self._create_chunk(
                        chunk_text, 
                        len(chunks),
                        metadata,
                        file_info
                    ))
                    current_chunk = []
                    current_length = 0
                
                # 分割超长句子
                sub_chunks = self._split_very_long_sentence(sentence, metadata, file_info)
                chunks.extend(sub_chunks)
                continue
            
            # 正常处理：如果添加当前句子会超过max_chunk_size，保存当前块
            if current_length + sent_length > self.max_chunk_size:
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(self._create_chunk(
                        chunk_text, 
                        len(chunks),
                        metadata,
                        file_info
                    ))
                
                # 开始新块
                current_chunk = [sentence]
                current_length = sent_length
            else:
                current_chunk.append(sentence)
                current_length += sent_length
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(self._create_chunk(
                chunk_text, 
                len(chunks),
                metadata,
                file_info
            ))
        
        return chunks
    
    def _split_very_long_sentence(self, sentence: str, metadata: Dict, file_info: Dict) -> List[TextChunk]:
        """
        分割超长句子
        
        Args:
            sentence: 超长句子文本
            metadata: 元数据
            file_info: 文件信息
            
        Returns:
            分块列表
        """
        chunks = []
        
        # 按逗号、分号等标点进一步分割
        parts = re.split(r'(?<=[，,；;])\s*', sentence)
        
        current_chunk = []
        current_length = 0
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            part_length = len(part)
            
            # 如果部分仍然太长，按固定大小分割
            if part_length > self.max_chunk_size:
                # 先把当前块保存
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(self._create_chunk(
                        chunk_text, 
                        len(chunks),
                        metadata,
                        file_info
                    ))
                    current_chunk = []
                    current_length = 0
                
                # 按固定大小分割
                for i in range(0, part_length, self.max_chunk_size):
                    sub_text = part[i:i + self.max_chunk_size]
                    chunks.append(self._create_chunk(
                        sub_text, 
                        len(chunks),
                        metadata,
                        file_info
                    ))
                continue
            
            # 正常处理
            if current_length + part_length > self.max_chunk_size:
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(self._create_chunk(
                        chunk_text, 
                        len(chunks),
                        metadata,
                        file_info
                    ))
                
                current_chunk = [part]
                current_length = part_length
            else:
                current_chunk.append(part)
                current_length += part_length
        
        # 处理最后一个块
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(self._create_chunk(
                chunk_text, 
                len(chunks),
                metadata,
                file_info
            ))
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        按句子分割文本（简单实现）
        
        Args:
            text: 文本
            
        Returns:
            句子列表
        """
        # 简单的句子分割（按句号、问号、感叹号分割）
        sentences = re.split(r'(?<=[。！？.!?])\s+', text)
        
        # 清理
        cleaned_sentences = []
        for sent in sentences:
            sent = sent.strip()
            if sent:
                cleaned_sentences.append(sent)
        
        return cleaned_sentences
    
    def _create_chunk(self, text: str, chunk_index: int, metadata: Dict, file_info: Dict) -> TextChunk:
        """
        创建文本分块
        
        Args:
            text: 分块文本
            chunk_index: 分块索引
            metadata: 元数据
            file_info: 文件信息
            
        Returns:
            TextChunk对象
        """
        chunk_id = f"{file_info['file_name']}_{chunk_index}"
        
        return TextChunk(
            text=text,
            metadata=metadata,
            chunk_id=chunk_id,
            start_pos=0,  # 简化实现，实际应该记录在原文中的位置
            end_pos=len(text),
            file_path=file_info['file_path'],
            file_name=file_info['file_name'],
            heading_context=self._extract_headings_from_metadata(metadata)
        )
    
    def _extract_headings_from_metadata(self, metadata: Dict) -> List[str]:
        """
        从元数据中提取标题上下文
        
        Args:
            metadata: 元数据
            
        Returns:
            标题列表
        """
        headings = []
        
        # 如果有标题元数据
        if 'title' in metadata:
            headings.append(metadata['title'])
        
        # 可以扩展从其他元数据字段提取标题
        
        return headings
    
    def process_extracted_contents(self, extracted_contents: List[Dict]) -> List[TextChunk]:
        """
        处理提取的内容列表
        
        Args:
            extracted_contents: 提取的内容列表
            
        Returns:
            所有分块列表
        """
        all_chunks = []
        
        for content in extracted_contents:
            text = content['content']
            metadata = content['metadata']
            file_info = content['file_info']
            
            chunks = self.chunk_text(text, metadata, file_info)
            all_chunks.extend(chunks)
        
        return all_chunks


if __name__ == "__main__":
    # 测试代码
    processor = ChunkProcessor(
        chunk_size=3000,
        chunk_overlap=300,
        min_chunk_size=2000,
        max_chunk_size=4000
    )
    
    # 测试文本
    test_text = """
    这是第一个段落。包含一些测试内容。
    这是同一个段落的第二句话。
    
    这是第二个段落。比第一个段落要长一些。
    这是第二段的第一句话。
    这是第二段的第二句话，稍微长一点。
    这是第二段的第三句话，也很长。
    
    这是一个非常长的段落，需要被分割成多个分块。这个段落包含很多内容，可能会超过最大分块大小。
    这是长段落的第二句话。
    这是长段落的第三句话，也很长。
    这是长段落的第四句话。
    这是长段落的第五句话，结束。
    """
    
    test_metadata = {'title': '测试文档'}
    test_file_info = {
        'file_path': '/tmp/test.md',
        'file_name': 'test.md',
        'file_size': 100,
        'modified_time': 1234567890
    }
    
    chunks = processor.chunk_text(test_text, test_metadata, test_file_info)
    
    print(f"分块数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n分块 {i+1} (ID: {chunk.chunk_id}):")
        print(f"文本长度: {len(chunk.text)}")
        print(f"文本预览: {chunk.text[:100]}...")
        print(f"文件: {chunk.file_name}")
        print(f"标题上下文: {chunk.heading_context}")