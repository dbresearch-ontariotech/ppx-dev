.PHONY: install build-layout-tree align-layout-tree serve

install:
	uv sync

build-layout-tree:
	uv run ppx-align process build-layout-tree ../output/paper/ --overwrite

align-layout-tree:
	uv run ppx-align process align-layout-tree ../output/paper/ --overwrite

serve:
	uv run ppx-align server start --data ../output --delay 500
