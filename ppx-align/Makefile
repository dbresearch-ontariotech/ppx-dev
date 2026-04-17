.PHONY: install build-layout-tree align-layout-tree serve

install:
	uv sync


build:
	uv run ppx-align build ../output/clip
	uv run ppx-align build ../output/resnet
	uv run ppx-align build ../output/rl
	uv run ppx-align build ../output/paddlepaddle

serve:
	uv run ppx-align serve ../output
