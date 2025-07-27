import os
from langchain_community.document_loaders import DirectoryLoader,TextLoader
from dotenv import load_dotenv,find_dotenv
from pathlib import Path
from langchain.schema import Document
from langchain.text_splitter import MarkdownTextSplitter
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentLoaderInvoke:
    def __init__(self):

        dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
        # 加载 .env 文件
        load_dotenv(dotenv_path=dotenv_path)

        # 1. 获取当前脚本的绝对路径
        current_script = Path(__file__).resolve()

        # 2. 向上导航到项目根目录（根据层级调整 parent 次数）
        project_root = current_script.parent.parent.parent
        document_path = project_root / os.getenv('DATA_PATH') / 'document'
        loader = DirectoryLoader(document_path, glob='**/*.md')
        self.documents = loader.load()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        # 创建Markdown文本分割器（按水平分隔线切割，排除代码块和引用块）
        # self.text_splitter = MarkdownTextSplitter(
        #     separators=["\n\n---\n\n", "\n\n", "\n", " ", ""],  # 优先按水平分隔线分割
        #     chunk_size=1000,
        #     chunk_overlap=0,  # Java版本没有重叠
        #     keep_separator=False  # 不保留分隔符
        # )


    def load_markdowns(self):
        document_list = []

        for document in self.documents:
            # 获取文件名
            filename = os.path.basename(document.metadata["source"])

            # 提取状态（假设文件名格式为 "xxx-状态.md"）
            # status_match = re.search(r'-([^\-]+)\.md$', filename)
            # status = status_match.group(1) if status_match else "未知状态"
            status = filename[filename.rfind('-') + 1: filename.rfind('.')]
            split_docs = self.text_splitter.split_documents([document])
            for split_doc in split_docs:
                split_doc.metadata.update({
                    "filename": filename,
                    "status": status,
                    "source": document.metadata["source"],
                })
            document_list.extend(split_docs)
        return document_list
