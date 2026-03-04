"""
BGE-M3 API客户端
封装对LM Studio BGE-M3嵌入模型的HTTP API调用
"""

import requests
import time
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BGE_M3_Config:
    """BGE-M3配置类"""
    base_url: str = "http://192.168.1.4:1234"
    model_name: str = "text-embedding-bge-m3"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    batch_size: int = 10  # 批量处理大小
    max_workers: int = 4  # 并发工作线程数


@dataclass
class EmbeddingRequest:
    """嵌入请求"""
    text: str
    model: str = "text-embedding-bge-m3"


@dataclass
class EmbeddingResponse:
    """嵌入响应"""
    embedding: List[float]
    text: str
    dimension: int = 1024
    request_time_ms: Optional[float] = None


class BGE_M3_Client:
    """BGE-M3 API客户端"""
    
    def __init__(self, config: Optional[BGE_M3_Config] = None):
        """
        初始化BGE-M3客户端
        
        Args:
            config: BGE-M3配置，如果为None则使用默认配置
        """
        self.config = config or BGE_M3_Config()
        self.embedding_endpoint = f"{self.config.base_url}/v1/embeddings"
        self._session = requests.Session()
        
        # 配置会话
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3
        )
        self._session.mount('http://', adapter)
        self._session.mount('https://', adapter)
        
        logger.info(f"初始化BGE-M3客户端: {self.embedding_endpoint}")
        logger.info(f"模型名称: {self.config.model_name}")
        logger.info(f"超时设置: {self.config.timeout}秒")
    
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送HTTP请求并处理重试
        
        Args:
            payload: 请求负载
            
        Returns:
            响应数据
            
        Raises:
            Exception: 请求失败
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()
                
                response = self._session.post(
                    self.embedding_endpoint,
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                
                request_time = (time.time() - start_time) * 1000  # 转换为毫秒
                data = response.json()
                
                logger.debug(f"API请求成功: {request_time:.2f}ms, 尝试 {attempt + 1}")
                return data, request_time
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"连接错误 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                logger.error(f"HTTP错误 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if response.status_code >= 400 and response.status_code < 500:
                    # 客户端错误，不重试
                    break
                    
            except Exception as e:
                last_exception = e
                logger.error(f"未知错误 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
            
            # 等待后重试
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (attempt + 1)
                logger.info(f"等待 {delay:.1f}秒后重试...")
                time.sleep(delay)
        
        # 所有重试都失败
        error_msg = f"API请求失败，已重试{self.config.max_retries}次"
        logger.error(error_msg)
        if last_exception:
            raise Exception(f"{error_msg}: {last_exception}")
        else:
            raise Exception(error_msg)
    
    def get_embedding(self, text: str) -> EmbeddingResponse:
        """
        获取单个文本的嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            EmbeddingResponse对象
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        payload = {
            "model": self.config.model_name,
            "input": text.strip()
        }
        
        try:
            data, request_time = self._make_request(payload)
            
            # 解析响应
            if "data" not in data or not data["data"]:
                raise ValueError("API响应格式错误: 缺少data字段")
            
            embedding_data = data["data"][0]
            if "embedding" not in embedding_data:
                raise ValueError("API响应格式错误: 缺少embedding字段")
            
            embedding = embedding_data["embedding"]
            
            # 验证向量维度
            if len(embedding) != 1024:
                logger.warning(f"向量维度不是1024: {len(embedding)}")
            
            return EmbeddingResponse(
                embedding=embedding,
                text=text,
                dimension=len(embedding),
                request_time_ms=request_time
            )
            
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {e}")
            raise
    
    def get_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResponse]:
        """
        批量获取嵌入向量（顺序处理）
        
        Args:
            texts: 文本列表
            
        Returns:
            EmbeddingResponse对象列表
        """
        if not texts:
            return []
        
        results = []
        total_texts = len(texts)
        
        logger.info(f"开始批量处理 {total_texts} 个文本")
        
        for i, text in enumerate(texts, 1):
            try:
                result = self.get_embedding(text)
                results.append(result)
                
                if i % 10 == 0 or i == total_texts:
                    logger.info(f"处理进度: {i}/{total_texts} ({i/total_texts*100:.1f}%)")
                    
            except Exception as e:
                logger.error(f"处理第 {i} 个文本失败: {e}")
                # 可以选择跳过失败项或抛出异常
                raise
        
        logger.info(f"批量处理完成: {len(results)}/{total_texts} 成功")
        return results
    
    def get_embeddings_concurrent(self, texts: List[str]) -> List[EmbeddingResponse]:
        """
        并发获取嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            EmbeddingResponse对象列表
        """
        if not texts:
            return []
        
        total_texts = len(texts)
        logger.info(f"开始并发处理 {total_texts} 个文本")
        
        results = []
        failed_texts = []
        
        # 分批处理
        batches = [texts[i:i + self.config.batch_size] 
                  for i in range(0, len(texts), self.config.batch_size)]
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_text = {}
            valid_texts = []
            
            # 过滤空文本
            for batch_idx, batch in enumerate(batches):
                for text in batch:
                    if text and text.strip():  # 过滤空文本
                        future = executor.submit(self.get_embedding, text)
                        future_to_text[future] = text
                        valid_texts.append(text)
                    else:
                        # 记录空文本但跳过处理
                        logger.debug(f"跳过空文本: 索引 {len(valid_texts)}")
                        failed_texts.append(text)
            
            valid_total = len(valid_texts)
            logger.info(f"实际处理 {valid_total} 个有效文本 (过滤了 {total_texts - valid_total} 个空文本)")
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_text):
                completed += 1
                text = future_to_text[future]
                
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"处理文本失败: {text[:50]}... - {e}")
                    failed_texts.append(text)
                
                if completed % 10 == 0 or completed == valid_total:
                    logger.info(f"并发处理进度: {completed}/{valid_total} ({completed/valid_total*100:.1f}%)")
        
        if failed_texts:
            logger.warning(f"有 {len(failed_texts)} 个文本处理失败")
        
        logger.info(f"并发处理完成: {len(results)}/{total_texts} 成功")
        return results
    
    def test_connectivity(self) -> bool:
        """
        测试API连通性
        
        Returns:
            bool: 是否连通成功
        """
        try:
            test_text = "测试API连通性"
            result = self.get_embedding(test_text)
            
            if result.dimension == 1024:
                logger.info(f"✅ API连通性测试通过，向量维度: {result.dimension}")
                return True
            else:
                logger.warning(f"⚠️ API连通性测试通过但维度异常: {result.dimension}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API连通性测试失败: {e}")
            return False
    
    def close(self):
        """关闭会话"""
        if self._session:
            self._session.close()
            logger.info("BGE-M3客户端会话已关闭")


# 单例模式，便于全局使用
_default_client: Optional[BGE_M3_Client] = None

def get_default_client() -> BGE_M3_Client:
    """获取默认客户端实例"""
    global _default_client
    if _default_client is None:
        _default_client = BGE_M3_Client()
    return _default_client


if __name__ == "__main__":
    # 测试代码
    client = BGE_M3_Client()
    
    # 测试连通性
    if client.test_connectivity():
        print("✅ BGE-M3客户端测试通过")
        
        # 测试单个文本
        test_text = "这是一个测试文本，用于验证BGE-M3嵌入模型"
        result = client.get_embedding(test_text)
        print(f"单个文本测试:")
        print(f"  文本: {test_text[:50]}...")
        print(f"  维度: {result.dimension}")
        print(f"  请求时间: {result.request_time_ms:.2f}ms")
        print(f"  向量前3个值: {result.embedding[:3]}")
        
        # 测试批量处理
        test_texts = [
            "第一个测试文本",
            "第二个测试文本，稍微长一些",
            "第三个测试文本，包含一些中文内容"
        ]
        
        results = client.get_embeddings_batch(test_texts)
        print(f"\n批量处理测试:")
        print(f"  处理数量: {len(results)}/{len(test_texts)}")
        
        client.close()
    else:
        print("❌ BGE-M3客户端测试失败")