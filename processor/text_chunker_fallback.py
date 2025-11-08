import re
from typing import List, Tuple

from config.settings import CHUNK_SIZE, OVERLAP, MAX_TEXT_LENGTH

try:
    import hanlp
    HANLP_AVAILABLE = True
except ImportError:
    HANLP_AVAILABLE = False

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


class ChineseTextChunker:
    """中文文本分块器，将长文本分割成带有重叠的文本块"""

    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP, max_text_length: int = MAX_TEXT_LENGTH):
        """
        初始化分块器

        Args:
            chunk_size: 每个文本块的目标大小（tokens数量）
            overlap: 相邻文本块的重叠大小（tokens数量）
            max_text_length: 最大文本长度
        """
        if chunk_size <= overlap:
            raise ValueError("chunk_size必须大于overlap")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_text_length = max_text_length

        # 选择可用的分词器
        if HANLP_AVAILABLE:
            print("使用HanLP分词器")
            self.tokenizer = hanlp.load(hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH)
            self.use_hanlp = True
        elif JIEBA_AVAILABLE:
            print("使用Jieba分词器")
            self.use_hanlp = False
        else:
            raise ImportError("需要安装hanlp或jieba")

    def process_files(self, file_contents: List[Tuple[str, str]]) -> List[Tuple[str, str, List[List[str]]]]:
        """
        处理多个文件的内容

        Args:
            file_contents: List of (filename, content) tuples

        Returns:
            List of (filename, content, chunks) tuples
        """
        results = []
        for filename, content in file_contents:
            chunks = self.chunk_text(content)
            results.append((filename, content, chunks))
        return results

    def _preprocess_large_text(self, text: str) -> List[str]:
        """
        预处理过大的文本，将其分割成较小的段落
        """
        if len(text) <= self.max_text_length:
            return [text]

        # 计算合适的段落大小
        target_segment_size = min(self.max_text_length, max(10000, self.max_text_length // 2))

        # 首先按段落分割
        paragraphs = text.split('\n\n')

        # 如果段落数量很少，尝试按单个换行符分割
        if len(paragraphs) < 5:
            paragraphs = text.split('\n')

        # 重新组合段落
        processed_segments = []
        current_segment = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果当前段落本身就超长
            if len(para) > target_segment_size:
                if current_segment:
                    processed_segments.append(current_segment)
                    current_segment = ""

                split_paras = self._split_long_paragraph(para, target_segment_size)
                processed_segments.extend(split_paras)

            else:
                if len(current_segment) + len(para) + 2 > target_segment_size:
                    if current_segment:
                        processed_segments.append(current_segment)
                    current_segment = para
                else:
                    if current_segment:
                        current_segment += "\n\n" + para
                    else:
                        current_segment = para

        if current_segment:
            processed_segments.append(current_segment)

        return processed_segments

    def _split_long_paragraph(self, text: str, max_size: int) -> List[str]:
        """分割超长段落"""
        if len(text) <= max_size:
            return [text]

        # 按句子分割
        sentences = re.split(r'([。！？.!?])', text)

        # 重新组合句子和标点
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
            if sentence.strip():
                combined_sentences.append(sentence + punctuation)

        if not combined_sentences:
            result = []
            for i in range(0, len(text), max_size):
                result.append(text[i:i + max_size])
            return result

        # 重新组合句子
        segments = []
        current_segment = ""

        for sentence in combined_sentences:
            if len(sentence) > max_size:
                if current_segment:
                    segments.append(current_segment)
                    current_segment = ""

                for i in range(0, len(sentence), max_size):
                    segments.append(sentence[i:i + max_size])
            else:
                if len(current_segment) + len(sentence) > max_size:
                    if current_segment:
                        segments.append(current_segment)
                    current_segment = sentence
                else:
                    current_segment += sentence

        if current_segment:
            segments.append(current_segment)

        return segments

    def _safe_tokenize(self, text: str) -> List[str]:
        """安全的分词方法"""
        try:
            if len(text) > self.max_text_length:
                # 对于超长文本，简单按字符分割
                return list(text)

            if self.use_hanlp:
                tokens = self.tokenizer(text)
            else:
                # 使用jieba分词
                tokens = list(jieba.cut(text))

            return tokens if tokens else []
        except Exception as e:
            print(f"分词失败: {e}，使用简单字符分割")
            return list(text)

    def chunk_text(self, text: str) -> List[List[str]]:
        """
        将单个文本分割成块
        """
        if not text or len(text) < self.chunk_size / 10:
            tokens = self._safe_tokenize(text)
            return [tokens] if tokens else []

        # 预处理过大文本
        text_segments = self._preprocess_large_text(text)

        # 处理每个文本段落
        all_chunks = []
        for segment in text_segments:
            segment_chunks = self._chunk_single_segment(segment)
            all_chunks.extend(segment_chunks)

        return all_chunks

    def _chunk_single_segment(self, text: str) -> List[List[str]]:
        """处理单个文本段落的分块"""
        if not text:
            return []

        # 先将整个文本分词
        all_tokens = self._safe_tokenize(text)
        if not all_tokens:
            return []

        chunks = []
        start_pos = 0

        while start_pos < len(all_tokens):
            # 确定当前块的结束位置
            end_pos = min(start_pos + self.chunk_size, len(all_tokens))

            # 如果不是最后一块，尝试在句子边界结束
            if end_pos < len(all_tokens):
                sentence_end = self._find_next_sentence_end(all_tokens, end_pos)
                if sentence_end <= start_pos + self.chunk_size + 100:
                    end_pos = sentence_end

            # 提取当前块
            chunk = all_tokens[start_pos:end_pos]
            if chunk:
                chunks.append(chunk)

            if end_pos >= len(all_tokens):
                break

            # 计算下一块的起始位置（考虑重叠）
            overlap_start = max(start_pos, end_pos - self.overlap)
            next_sentence_start = self._find_previous_sentence_end(all_tokens, overlap_start)

            if next_sentence_start > start_pos and next_sentence_start < end_pos:
                start_pos = next_sentence_start
            else:
                start_pos = overlap_start

            if start_pos >= end_pos:
                start_pos = end_pos

        return chunks

    def _is_sentence_end(self, token: str) -> bool:
        """判断token是否为句子结束符"""
        return token in ['。', '！', '？', '.', '!', '?']

    def _find_next_sentence_end(self, tokens: List[str], start_pos: int) -> int:
        """从指定位置向后查找句子结束位置"""
        for i in range(start_pos, len(tokens)):
            if self._is_sentence_end(tokens[i]):
                return i + 1
        return len(tokens)

    def _find_previous_sentence_end(self, tokens: List[str], start_pos: int) -> int:
        """从指定位置向前查找句子结束位置"""
        for i in range(start_pos - 1, -1, -1):
            if self._is_sentence_end(tokens[i]):
                return i + 1
        return 0
