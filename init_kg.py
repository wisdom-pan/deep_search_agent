#!/usr/bin/env python3
"""
初始化知识图谱数据
"""
import os
import sys

from server.server_config.database import get_db_manager
from processor.document_processor import DocumentProcessor
from graph.extraction.entity_extractor import EntityRelationExtractor
from graph.extraction.graph_writer import GraphWriter
from graph.structure.struct_builder import GraphStructureBuilder
from graph.indexing.entity_indexer import EntityIndexManager
from graph.indexing.chunk_indexer import ChunkIndexManager
from model.get_models import get_llm_model
from config.prompt import (
    system_template_build_graph,
    human_template_build_graph
)
from config.settings import (
    entity_types,
    relationship_types
)
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_knowledge_graph():
    """初始化知识图谱数据"""
    try:
        logger.info("开始初始化知识图谱...")

        # 获取数据库连接
        db_manager = get_db_manager()

        # 检查是否已有数据 - 注释掉以强制重新初始化
        # existing_data = db_manager.execute_query("MATCH (n) RETURN count(n) as count")
        # if existing_data is not None and not existing_data.empty and len(existing_data) > 0 and int(existing_data.iloc[0]['count']) > 0:
        #     logger.info(f"数据库中已有 {existing_data.iloc[0]['count']} 个节点，跳过初始化")
        #     return
        logger.info("强制重新初始化知识图谱...")

        # 获取文件目录
        files_dir = os.path.join(os.path.dirname(__file__), "files", "txt文件")
        if not os.path.exists(files_dir):
            logger.error(f"文件目录不存在: {files_dir}")
            return
        logger.info(f"使用文件目录: {files_dir}")

        # 初始化处理器
        doc_processor = DocumentProcessor(directory_path=files_dir)
        llm = get_llm_model()
        entity_extractor = EntityRelationExtractor(
            llm=llm,
            system_template=system_template_build_graph,
            human_template=human_template_build_graph,
            entity_types=entity_types,
            relationship_types=relationship_types
        )

        # 初始化图结构构建器和写入器
        structure_builder = GraphStructureBuilder()
        graph_writer = GraphWriter()

        # 初始化索引管理器
        entity_indexer = EntityIndexManager()
        chunk_indexer = ChunkIndexManager()

        # 处理所有txt文件
        logger.info(f"开始处理文档目录: {files_dir}")

        try:
            # 使用DocumentProcessor处理整个目录
            logger.info(f"  - 分块处理...")
            processed_docs = doc_processor.process_directory(file_extensions=['.txt'], recursive=True)

            logger.info(f"  - 找到 {len(processed_docs)} 个文档")

            if not processed_docs:
                logger.warning("没有找到可处理的文档")
                return

            logger.info(f"  - 创建图结构...")

            # 创建文档节点和文本块节点
            all_chunks_with_data = []
            for doc in processed_docs:
                filename = doc.get('filename', 'unknown')
                chunks = doc.get('chunks', [])

                if not chunks:
                    continue

                # 创建文档节点
                structure_builder.create_document(
                    type='.txt',
                    uri=f"file://{files_dir}/{filename}",
                    file_name=filename,
                    domain="document"
                )

                # 创建文本块节点和关系
                chunks_data = structure_builder.create_relation_between_chunks(filename, chunks)
                all_chunks_with_data.extend(chunks_data)

                logger.info(f"  - 文档 {filename} 创建了 {len(chunks)} 个文本块节点")

            if not all_chunks_with_data:
                logger.warning("没有生成有效的文本块节点")
                return

            logger.info(f"  - 总共创建 {len(all_chunks_with_data)} 个文本块节点")
            logger.info(f"  - 提取实体和关系...")

            # 使用正确的EntityRelationExtractor方法
            # 首先准备数据格式
            file_contents = []
            for doc in processed_docs:
                filename = doc.get('filename', 'unknown')
                chunks = doc.get('chunks', [])
                file_contents.append((filename, '.txt', chunks))

            # 使用process_chunks方法处理
            processed_results = entity_extractor.process_chunks(file_contents)

            # 准备GraphWriter需要的数据格式
            logger.info(f"  - 准备写入图数据库的数据...")

            # 重新构建正确的数据结构，将chunks和extraction_results对应起来
            writer_data = []

            logger.info(f"  - processed_docs 长度: {len(processed_docs)}")
            logger.info(f"  - processed_results 长度: {len(processed_results)}")
            logger.info(f"  - processed_results 内容: {processed_results}")

            for i, doc in enumerate(processed_docs):
                filename = doc.get('filename', 'unknown')
                chunks = doc.get('chunks', [])

                # 获取对应的提取结果
                if i < len(processed_results) and len(processed_results[i]) >= 4:
                    extraction_results = processed_results[i][3]  # 提取结果在第4个位置

                    # 获取对应的chunks_with_hash
                    chunks_with_hash_for_file = []
                    # 找到对应的chunks_with_hash
                    for chunk_data in all_chunks_with_data:
                        # 检查chunk_id是否匹配（通过内容匹配）
                        for chunk in chunks:
                            chunk_content = ''.join(chunk)
                            if chunk_data['chunk_doc'].page_content == chunk_content:
                                chunks_with_hash_for_file.append(chunk_data)
                                break

                    # 确保chunks和extraction_results数量匹配
                    if len(chunks_with_hash_for_file) > 0:
                        # 调整数量以匹配
                        min_length = min(len(chunks_with_hash_for_file), len(extraction_results))
                        chunks_with_hash_for_file = chunks_with_hash_for_file[:min_length]
                        extraction_results = extraction_results[:min_length]

                        writer_data.append((filename, '.txt', chunks_with_hash_for_file, extraction_results))
                        logger.info(f"  - 文件 {filename} 准备写入 {len(chunks_with_hash_for_file)} 个chunks")
                    else:
                        logger.warning(f"  - 文件 {filename} chunks_with_hash_for_file 为空，跳过")
            else:
                logger.warning(f"  - 文件 {filename} extraction_results 无效，跳过")

            # 使用GraphWriter的专用方法写入数据
            logger.info(f"  - writer_data 长度: {len(writer_data)}")
            if writer_data:
                logger.info(f"  - 开始写入图数据库，共 {len(writer_data)} 个文件")
                for i, data in enumerate(writer_data):
                    logger.info(f"    - 文件 {i+1}: {data[0]}, chunks: {len(data[2])}, extractions: {len(data[3]) if len(data) > 3 else 0}")
                graph_writer.process_and_write_graph_documents(writer_data)
            else:
                logger.warning("  - writer_data 为空，没有数据写入图数据库")

                # 统计写入的节点和关系数量
                final_count = db_manager.execute_query("MATCH (n) RETURN count(n) as count")
                if final_count is not None and not final_count.empty and len(final_count) > 0:
                    total_nodes = final_count.iloc[0]['count']

                    entity_count = db_manager.execute_query("MATCH (e:__Entity__) RETURN count(e) as count")
                    chunk_count = db_manager.execute_query("MATCH (c:__Chunk__) RETURN count(c) as count")
                    doc_count = db_manager.execute_query("MATCH (d:__Document__) RETURN count(d) as count")
                    rel_count = db_manager.execute_query("MATCH ()-[r]->() RETURN count(r) as count")

                    entity_num = entity_count.iloc[0]['count'] if entity_count is not None and not entity_count.empty else 0
                    chunk_num = chunk_count.iloc[0]['count'] if chunk_count is not None and not chunk_count.empty else 0
                    doc_num = doc_count.iloc[0]['count'] if doc_count is not None and not doc_count.empty else 0
                    rel_num = rel_count.iloc[0]['count'] if rel_count is not None and not rel_count.empty else 0

                    logger.info(f"  - 写入了总计 {total_nodes} 个节点")
                    logger.info(f"    - 实体节点: {entity_num}")
                    logger.info(f"    - 文本块节点: {chunk_num}")
                    logger.info(f"    - 文档节点: {doc_num}")
                    logger.info(f"    - 关系: {rel_num}")
                else:
                    logger.warning("  - 无法统计写入的节点数量")
            logger.info(f"  - 创建向量索引...")

            # 创建向量索引
            try:
                entity_vector_store = entity_indexer.create_entity_index()
                if entity_vector_store:
                    logger.info("  - 实体向量索引创建成功")
                else:
                    logger.warning("  - 实体向量索引创建失败或没有实体需要处理")
            except Exception as e:
                logger.warning(f"  - 实体向量索引创建出错: {e}")

            try:
                chunk_vector_store = chunk_indexer.create_chunk_index()
                if chunk_vector_store:
                    logger.info("  - 文本块向量索引创建成功")
                else:
                    logger.warning("  - 文本块向量索引创建失败或没有文本块需要处理")
            except Exception as e:
                logger.warning(f"  - 文本块向量索引创建出错: {e}")

            logger.info("所有文档处理完成")

        except Exception as e:
            logger.error(f"处理文档时出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return

        # 统计结果
        final_count = db_manager.execute_query("MATCH (n) RETURN count(n) as count")
        if final_count is not None and not final_count.empty and len(final_count) > 0:
            logger.info(f"初始化完成！数据库中共有 {final_count.iloc[0]['count']} 个节点")
        else:
            logger.warning("初始化完成，但没有统计到节点数量")

    except Exception as e:
        logger.error(f"初始化知识图谱失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    init_knowledge_graph()