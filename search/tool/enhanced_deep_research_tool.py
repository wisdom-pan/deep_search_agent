"""
增强版深度研究工具
支持图文混排、图表生成、数学公式和实时进度显示
"""

import time
import os
import io
import base64
import json
import re
import asyncio
from typing import Dict, List, Any, AsyncGenerator, Optional, Union
from datetime import datetime
import traceback

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PIL import Image
import sympy as sp
from sympy import latex, sympify

from search.tool.deep_research_tool import DeepResearchTool


class EnhancedDeepResearchTool(DeepResearchTool):
    """
    增强版深度研究工具：
    1. 支持图文混排（Markdown + 图表）
    2. 支持数学公式（LaTeX）
    3. 自动生成数据可视化图表
    4. 实时进度报告
    5. 增强的引用和参考文献系统
    """

    def __init__(self):
        """初始化增强版深度研究工具"""
        super().__init__()

        # 设置图表输出目录
        self.images_dir = "./static/images"
        self.ensure_images_dir()

        # 进度跟踪
        self.current_stage = "初始化"
        self.stage_progress = 0
        self.total_stages = 10
        self.progress_callback = None
        self.execution_steps = []

    def ensure_images_dir(self):
        """确保图片目录存在"""
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(f"{self.images_dir}/charts", exist_ok=True)
        os.makedirs(f"{self.images_dir}/formulas", exist_ok=True)
        os.makedirs(f"{self.images_dir}/analysis", exist_ok=True)

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    def update_progress(self, stage: str, progress: int, message: str = "", step_type: str = "progress"):
        """更新进度并记录执行步骤"""
        self.current_stage = stage
        self.stage_progress = progress

        # 记录执行步骤
        step = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "progress": progress,
            "message": message,
            "type": step_type
        }
        self.execution_steps.append(step)

        # 调用回调函数
        if self.progress_callback:
            self.progress_callback(step)

        self._log(f"[进度] {stage}: {progress}% - {message}")

    def generate_chart(self, data: List[Dict], chart_type: str = "bar",
                      title: str = "数据图表", xlabel: str = "X轴", ylabel: str = "Y轴") -> str:
        """
        生成图表并返回Markdown格式的图片标签

        Args:
            data: 数据列表，格式为 [{"label": "标签", "value": 数值}, ...]
            chart_type: 图表类型 (bar, line, pie, scatter)
            title: 图表标题
            xlabel: X轴标签
            ylabel: Y轴标签

        Returns:
            str: Markdown格式的图片标签
        """
        try:
            self.update_progress("生成图表", 85, f"正在生成{chart_type}类型图表: {title}", "chart")

            # 创建图表
            fig, ax = plt.subplots(figsize=(10, 6))

            # 处理数据
            labels = [item.get("label", "") for item in data]
            values = [item.get("value", 0) for item in data]

            # 设置颜色主题
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

            # 根据类型绘制图表
            if chart_type == "bar":
                bars = ax.bar(labels, values, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
                # 添加数值标签
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.2f}', ha='center', va='bottom', fontsize=10)

            elif chart_type == "line":
                ax.plot(labels, values, marker='o', linewidth=3, markersize=10, color='#2E86C1')
                ax.fill_between(labels, values, alpha=0.3, color='#85C1E9')
                # 添加数值标签
                for i, (label, value) in enumerate(zip(labels, values)):
                    ax.annotate(f'{value:.2f}', (i, value), textcoords="offset points",
                               xytext=(0,10), ha='center', fontsize=10)

            elif chart_type == "pie":
                wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                                  startangle=90, colors=colors)
                # 美化文字
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')

            elif chart_type == "scatter":
                scatter = ax.scatter(labels, values, s=200, alpha=0.7, c=colors, edgecolors='black')
                # 添加趋势线
                if len(values) > 1:
                    z = np.polyfit(range(len(values)), values, 1)
                    p = np.poly1d(z)
                    ax.plot(labels, p(range(len(values))), "r--", alpha=0.8, linewidth=2, label='趋势线')
                    ax.legend()

            # 设置标题和标签
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
            ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')

            # 旋转X轴标签以避免重叠
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            # 生成唯一文件名
            timestamp = int(time.time() * 1000)
            chart_id = f"chart_{chart_type}_{timestamp}"
            filename = f"{self.images_dir}/charts/{chart_id}.png"

            # 保存图表
            plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()

            # 返回Markdown格式的图片标签
            return f"\n\n<div align='center'>\n\n![{title}]({filename})\n\n*图1: {title}*\n\n</div>\n\n"

        except Exception as e:
            self._log(f"生成图表失败: {str(e)}")
            return f"\n\n*图表生成失败: {str(e)}*\n\n"

    def render_latex_formula(self, formula: str, label: str = "公式") -> str:
        """
        渲染LaTeX数学公式

        Args:
            formula: LaTeX格式的数学公式
            label: 公式标签

        Returns:
            str: Markdown格式的公式
        """
        try:
            self.update_progress("生成公式", 87, f"正在渲染数学公式: {label}", "formula")

            # 验证公式
            try:
                sympify(formula)
            except:
                # 如果验证失败，仍然尝试渲染
                pass

            # 生成LaTeX渲染图
            fig = plt.figure(figsize=(12, 3))
            fig.text(0.5, 0.5, f'$${formula}$$', fontsize=24, ha='center', va='center')
            fig.patch.set_facecolor('white')

            # 生成文件名
            timestamp = int(time.time() * 1000)
            formula_id = f"formula_{timestamp}"
            filename = f"{self.images_dir}/formulas/{formula_id}.png"

            # 保存公式
            plt.savefig(filename, dpi=150, bbox_inches='tight', transparent=False, facecolor='white')
            plt.close()

            # 返回Markdown格式
            return f"\n\n<div align='center'>\n\n**{label}**\n\n![{label}]({filename})\n\n$${formula}$$\n\n</div>\n\n"

        except Exception as e:
            # 如果渲染失败，尝试使用纯文本
            return f"\n\n**{label}:** ${formula}$\n\n"

    def analyze_data_for_charts(self, content: str) -> List[Dict]:
        """
        从内容中提取可可视化的数据

        Args:
            content: 文本内容

        Returns:
            List[Dict]: 图表数据列表
        """
        charts = []

        # 匹配数字列表
        number_pattern = r'(\w+[^,，:：])\s*[:：]\s*([0-9]+\.?[0-9]*)'
        matches = re.findall(number_pattern, content)

        if matches and len(matches) >= 3:
            data = [{"label": label.strip(), "value": float(val)} for label, val in matches]
            charts.append({
                "type": "bar",
                "data": data,
                "title": "数据分析 - 数值分布",
                "description": "从文本中提取的数值数据可视化",
                "xlabel": "项目",
                "ylabel": "数值"
            })

        # 匹配百分比
        percent_pattern = r'(\w+[^,，:：])\s*[:：]\s*([0-9]+)%'
        percent_matches = re.findall(percent_pattern, content)

        if percent_matches and len(percent_matches) >= 3:
            data = [{"label": label.strip(), "value": float(val)} for label, val in percent_matches]
            charts.append({
                "type": "pie",
                "data": data,
                "title": "占比分析 - 各部分比例",
                "description": "各部分占比情况分析",
                "xlabel": "",
                "ylabel": ""
            })

        # 匹配时间序列数据
        time_pattern = r'(\d{4}[-年]\d{1,2}[-月]?)\s*[:：]\s*([0-9]+\.?[0-9]*)'
        time_matches = re.findall(time_pattern, content)

        if time_matches and len(time_matches) >= 3:
            data = [{"label": time.strip(), "value": float(val)} for time, val in time_matches]
            charts.append({
                "type": "line",
                "data": data,
                "title": "趋势分析 - 时间序列",
                "description": "随时间变化的趋势分析",
                "xlabel": "时间",
                "ylabel": "数值"
            })

        return charts

    def extract_and_render_formulas(self, content: str) -> str:
        """
        提取并渲染数学公式

        Args:
            content: 文本内容

        Returns:
            str: 包含渲染公式的文本
        """
        # 匹配LaTeX公式标记 $$...$$ 或 $...$
        formula_patterns = [
            r'\$\$([^$]+)\$\$(?![$])',  # $$...$$
            r'\$([^$\n]+)\$(?![$])'     # $...$
        ]

        formulas = []
        for pattern in formula_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            formulas.extend(matches)

        if not formulas:
            # 尝试匹配常见的数学表达式
            math_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^\\n]+)'
            formulas = re.findall(math_pattern, content)

        result = content
        formula_count = 0

        for formula in formulas[:5]:  # 限制最多5个公式
            formula_count += 1
            formula_clean = formula.strip()
            rendered = self.render_latex_formula(
                formula_clean,
                f"公式 {formula_count}"
            )
            result += rendered

        return result

    def enhance_content_with_visualizations(self, content: str) -> str:
        """
        增强内容，添加图表和可视化

        Args:
            content: 原始内容

        Returns:
            str: 包含图表的增强内容
        """
        self.update_progress("分析数据", 82, "正在分析内容中的数据模式...", "analysis")

        # 分析数据并生成图表
        charts = self.analyze_data_for_charts(content)

        enhanced_content = content

        if charts:
            enhanced_content += "\n\n## 📊 数据可视化分析\n"

            for i, chart_info in enumerate(charts[:3], 1):  # 最多添加3个图表
                enhanced_content += f"\n### {i}. {chart_info['title']}\n\n"
                enhanced_content += f"*说明:* {chart_info['description']}\n\n"

                chart_md = self.generate_chart(
                    data=chart_info["data"],
                    chart_type=chart_info["type"],
                    title=chart_info["title"],
                    xlabel=chart_info.get("xlabel", ""),
                    ylabel=chart_info.get("ylabel", "")
                )
                enhanced_content += chart_md

                # 添加数据分析解读
                enhanced_content += self._interpret_chart(chart_info)
                enhanced_content += "\n"

        # 提取并渲染数学公式
        self.update_progress("渲染公式", 88, "正在渲染数学公式...", "formula")
        enhanced_content = self.extract_and_render_formulas(enhanced_content)

        # 添加数据总结
        if charts:
            enhanced_content += "\n---\n### 📈 数据分析总结\n\n"
            enhanced_content += "**关键发现:**\n"
            enhanced_content += "1. 以上图表基于文本内容自动生成，帮助理解数据分布和关系\n"
            enhanced_content += "2. 图表展示了主要数据特征，包括数值分布、占比和趋势\n"
            enhanced_content += "3. 建议结合具体场景进一步分析数据背后的原因\n\n"

        return enhanced_content

    def _interpret_chart(self, chart_info: Dict) -> str:
        """对图表进行解读"""
        interpretation = "\n**图表解读:**\n"

        if chart_info["type"] == "bar":
            data = chart_info["data"]
            max_item = max(data, key=lambda x: x["value"])
            min_item = min(data, item=lambda x: x["value"])
            interpretation += f"- 最大值: {max_item['label']} ({max_item['value']})\n"
            interpretation += f"- 最小值: {min_item['label']} ({min_item['value']})\n"
            interpretation += f"- 平均值: {sum(item['value'] for item in data) / len(data):.2f}\n"

        elif chart_info["type"] == "pie":
            data = chart_info["data"]
            total = sum(item["value"] for item in data)
            interpretation += f"- 总计: {total}\n"
            for item in data:
                percentage = (item["value"] / total) * 100
                interpretation += f"- {item['label']}: {percentage:.1f}%\n"

        elif chart_info["type"] == "line":
            data = chart_info["data"]
            values = [item["value"] for item in data]
            trend = "上升" if values[-1] > values[0] else "下降"
            interpretation += f"- 总体趋势: {trend}\n"
            interpretation += f"- 起始值: {values[0]}, 结束值: {values[-1]}\n"

        return interpretation

    def generate_comprehensive_answer(self, query: str, retrieved_content: str,
                                     thinking_process: str) -> str:
        """
        生成综合性的答案，包含图表、公式和引用

        Args:
            query: 用户问题
            retrieved_content: 检索到的内容
            thinking_process: 思考过程

        Returns:
            str: 增强的答案
        """
        try:
            self.update_progress("生成答案", 80, "正在综合分析并生成可视化内容...", "answer")

            # 构建结构化答案
            answer_parts = []

            # 1. 问题分析
            answer_parts.append(f"## 📋 问题分析")
            answer_parts.append(f"**问题:** {query}")
            answer_parts.append(f"**分析时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            answer_parts.append(f"**执行步骤数:** {len(self.execution_steps)}")
            answer_parts.append("")

            # 2. 关键发现
            answer_parts.append(f"## 🔍 关键发现")
            key_points = self._extract_key_points(thinking_process)
            for i, point in enumerate(key_points, 1):
                answer_parts.append(f"{i}. {point}")
            answer_parts.append("")

            # 3. 详细分析
            answer_parts.append(f"## 📚 详细分析")
            answer_parts.append(retrieved_content)
            answer_parts.append("")

            # 4. 数据可视化
            self.update_progress("生成图表", 84, "正在生成数据可视化...", "visualization")
            enhanced_content = self.enhance_content_with_visualizations(retrieved_content)

            if enhanced_content != retrieved_content:
                answer_parts.append(f"## 📊 数据可视化与深度分析")
                answer_parts.append(enhanced_content)
                answer_parts.append("")

            # 5. 结论和建议
            answer_parts.append(f"## 💡 结论与建议")
            conclusions = self._generate_conclusions(query, retrieved_content)
            for i, conclusion in enumerate(conclusions, 1):
                answer_parts.append(f"{i}. {conclusion}")
            answer_parts.append("")

            # 6. 引用来源
            answer_parts.append(f"## 📖 参考来源")
            sources = self._extract_sources(retrieved_content)
            for i, source in enumerate(sources, 1):
                answer_parts.append(f"{i}. {source}")
            answer_parts.append("")

            # 7. 执行流程
            answer_parts.append(f"## 🔄 分析执行流程")
            for i, step in enumerate(self.execution_steps[-10:], 1):  # 显示最后10步
                answer_parts.append(f"{i}. [{step['stage']}] {step['message']}")
            answer_parts.append("")

            # 8. 生成时间戳
            answer_parts.append(f"---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                              f"分析步骤: {len(self.execution_steps)}*")

            final_answer = "\n".join(answer_parts)

            self.update_progress("完成", 100, "答案生成完成！", "complete")

            return final_answer

        except Exception as e:
            self._log(f"生成综合答案时出错: {str(e)}")
            error_msg = f"""## ⚠️ 答案生成过程遇到问题

**错误信息:** {str(e)}

**原始内容:**
{thinking_process}

{retrieved_content}
"""
            return error_msg

    def _extract_key_points(self, thinking: str) -> List[str]:
        """从思考过程中提取关键点"""
        lines = thinking.split('\n')
        key_points = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith('我需要') or line.startswith('通过') or
                        '重要' in line or '关键' in line or '发现' in line):
                key_points.append(line)
        return key_points[:5]

    def _generate_conclusions(self, query: str, content: str) -> List[str]:
        """生成结论和建议"""
        conclusions = [
            "基于现有信息，建议进一步收集相关数据以验证结论。",
            "当前分析提供了有价值的初步见解，需要更深入的研究。",
            "建议关注数据的时效性和准确性，确保决策依据可靠。",
            "可考虑结合更多维度的数据进行综合分析，提高结论的可靠性。"
        ]
        return conclusions

    def _extract_sources(self, content: str) -> List[str]:
        """提取引用来源"""
        sources = []
        if "Document" in content:
            sources.append("📄 知识库文档")
        if "社区" in content or "社区" in content:
            sources.append("🌐 社区讨论")
        if len(sources) == 0:
            sources.append("🔍 网络检索结果")
        return sources

    async def thinking_stream_enhanced(self, query: str) -> AsyncGenerator[Union[str, Dict], None]:
        """
        增强版流式思考过程，包含详细进度

        Args:
            query: 用户问题

        Returns:
            AsyncGenerator: 流式内容和状态更新
        """
        self.update_progress("开始分析", 0, "正在初始化分析流程...", "init")

        # 清空之前的执行步骤
        self.execution_steps = []

        try:
            # 调用父类的thinking_stream，但添加增强处理
            async for chunk in super().thinking_stream(query):
                # 解析chunk内容，更新进度
                if isinstance(chunk, str):
                    if "正在分析" in chunk:
                        self.update_progress("问题分析", 10, "分解问题并制定搜索策略...", "analysis")
                        yield {"type": "progress", "stage": "问题分析", "progress": 10, "message": "分解问题并制定搜索策略"}
                    elif "搜索" in chunk and ("第" in chunk or "轮" in chunk):
                        self.update_progress("信息检索", 40, f"正在搜索相关信息: {chunk[:50]}...", "search")
                        yield {"type": "progress", "stage": "信息检索", "progress": 40, "message": "正在搜索相关信息"}
                    elif "第" in chunk and "轮" in chunk:
                        self.update_progress("迭代分析", 60, f"进行多轮分析以获得全面答案", "iteration")
                        yield {"type": "progress", "stage": "迭代分析", "progress": 60, "message": "进行多轮分析"}
                    elif "思考" in chunk or "分析" in chunk:
                        self.update_progress("深度思考", 50, "正在进行深度思考和分析", "thinking")

                # 转发内容
                yield {"type": "content", "content": chunk}

            # 在最后添加增强的答案
            self.update_progress("生成可视化", 90, "正在生成图表和公式...", "visualization")
            yield {"type": "progress", "stage": "生成可视化", "progress": 90, "message": "正在生成图表和公式"}

            try:
                # 获取最终内容
                final_content = ""
                if hasattr(self, 'thinking_engine') and hasattr(self, 'all_retrieved_info'):
                    result = await self._async_generate_final_answer(
                        query, self.all_retrieved_info, ""
                    )
                    if result:
                        final_content = result

                # 增强内容
                if final_content:
                    yield {"type": "progress", "stage": "内容增强", "progress": 95, "message": "正在增强内容"}
                    enhanced = self.enhance_content_with_visualizations(final_content)
                    yield {"type": "content", "content": f"\n\n## 🎨 增强分析报告\n{enhanced}"}

            except Exception as e:
                self._log(f"增强内容时出错: {str(e)}")
                yield {"type": "error", "message": f"内容增强过程中出错: {str(e)}"}

            # 发送完成状态
            self.update_progress("完成", 100, "分析完成！", "complete")
            yield {"type": "complete", "stage": "完成", "progress": 100, "message": "分析完成"}

        except Exception as e:
            self._log(f"增强思考过程出错: {str(e)}")
            yield {"type": "error", "message": f"处理过程中出错: {str(e)}"}


if __name__ == "__main__":
    # 测试代码
    tool = EnhancedDeepResearchTool()

    # 测试图表生成
    test_data = [
        {"label": "项目A", "value": 100},
        {"label": "项目B", "value": 75},
        {"label": "项目C", "value": 50}
    ]
    chart = tool.generate_chart(test_data, "bar", "测试图表", "项目", "数值")
    print(chart)
