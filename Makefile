.PHONY: install

install:
	uv sync
	uv pip install paddlepaddle-gpu==3.2.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
	uv pip install -U "paddleocr[doc-parser]"
	uv pip install numpy==1.26.4
	cp -r patch/* .venv/


ocr:
	uv run ppx ocr run -o output ./tests/fixtures/paper.pdf

build-layout-tree:
	uv run ppx ocr build-layout-tree ./output/paper/ --overwrite

align-layout-tree:
	uv run ppx ocr align-layout-tree ./output/paper/ --overwrite

serve:
	uv run ppx server start --data ./output --delay 500

clean:
	rm -rf ./output
