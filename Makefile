install:
	uv sync
	uv pip install paddlepaddle-gpu==3.2.1 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
	uv pip install -U "paddleocr[doc-parser]"
	uv pip install numpy==1.26.4
	cp -r patch/* .venv/

start:
	@echo "Starting FastAPI backend..."
	uv run ppx server start --reload --data ./output & echo $$! > .dev.pids
	@echo "Starting Next.js frontend..."
	cd web && npm run dev & echo $$! >> .dev.pids
	@echo "Dev servers started. PIDs saved to .dev.pids"

stop:
	@if [ -f .dev.pids ]; then \
		while read pid; do \
			kill "$$pid" 2>/dev/null && echo "Killed $$pid" || echo "Process $$pid already stopped"; \
		done < .dev.pids; \
		rm -f .dev.pids; \
		echo "Dev servers stopped."; \
	else \
		echo "No .dev.pids file found. Are the servers running?"; \
	fi

.PHONY: install start stop
