install:
	uv sync
	uv pip install paddlepaddle-gpu==3.2.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
	uv pip install -U "paddleocr[doc-parser]"
	uv pip install numpy==1.26.4
	cp -r patch/* .venv/

.PHONY: install
