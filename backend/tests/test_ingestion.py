"""文件解析测试：PDF / PPTX / Markdown / 非法输入。"""
import pytest

from backend.ingestion import parse_file
from tests.fixture_files import (
    make_garbage_bytes,
    make_markdown_bytes,
    make_pdf_bytes,
    make_pptx_bytes,
)


def test_parse_pdf():
    text, title = parse_file(".pdf", make_pdf_bytes(), "os-notes.pdf")
    assert "Process Scheduling" in text
    assert title  # 元数据标题或文件名


def test_parse_pptx():
    text, title = parse_file(".pptx", make_pptx_bytes(), "slides.pptx")
    assert "Deadlock" in text
    assert "第1页" in text  # Markdown 友好的分页标记


def test_parse_markdown():
    text, title = parse_file(".md", make_markdown_bytes(), "note.md")
    assert "# 进程管理" in text
    assert "PCB" in text


def test_parse_unsupported_extension():
    with pytest.raises(ValueError):
        parse_file(".docx", b"x", "file.docx")


def test_parse_garbage_pdf_raises():
    with pytest.raises(ValueError):
        parse_file(".pdf", make_garbage_bytes(), "fake.pdf")


def test_parse_garbage_pptx_raises():
    with pytest.raises(ValueError):
        parse_file(".pptx", make_garbage_bytes(), "fake.pptx")
