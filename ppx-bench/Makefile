.PHONY: all ocr trees align corrupt align-noise benchmarks summary clean help

SAMPLES  := ../samples/en
OUTPUT   := ../output
DOCS     := $(notdir $(basename $(wildcard $(SAMPLES)/*.pdf)))
NOISE    := 0.01,0.02,0.03,0.04,0.05,0.1,0.2
SEED     := 42
GPUS     := $(shell nvidia-smi -L 2>/dev/null | wc -l)
GPUS     := $(if $(filter 0,$(GPUS)),1,$(GPUS))

help:
	@echo "Targets:"
	@echo "  all         Run the full pipeline (ocr → trees → align → corrupt → align-noise → benchmarks)"
	@echo "  ocr         Run OCR on each PDF in $(SAMPLES) (parallel across $(GPUS) GPUs)"
	@echo "  trees       Build layout-tree.parquet for each doc"
	@echo "  align       Build gold alignment.json for each doc (parallel, one GPU per doc)"
	@echo "  corrupt     Corrupt markdown for each doc at noise levels: $(NOISE)"
	@echo "  align-noise Run alignment for each noise level (parallel, one GPU per doc)"
	@echo "  benchmarks  benchmark + noise-benchmark + precision-recall-benchmark + summary"
	@echo "  summary     Print the benchmark summary"
	@echo "  clean       Remove $(OUTPUT)"
	@echo ""
	@echo "Config: DOCS=$(DOCS)"
	@echo "        NOISE=$(NOISE)"
	@echo "        GPUS=$(GPUS)"
	@echo "        SEED=$(SEED)"

all: ocr trees align corrupt align-noise benchmarks

ocr:
	@if [ -z "$(DOCS)" ]; then echo "No PDFs found in $(SAMPLES)" >&2; exit 1; fi
	@i=0; \
	for doc in $(DOCS); do \
		gpu=$$((i % $(GPUS))); \
		echo "[GPU $$gpu] OCR $$doc"; \
		CUDA_VISIBLE_DEVICES=$$gpu uv run --project ../ppx-ocr ppx-ocr -o $(OUTPUT) $(SAMPLES)/$$doc.pdf & \
		i=$$((i+1)); \
	done; \
	wait

trees:
	@for doc in $(DOCS); do \
		echo "[build-layout-tree] $$doc"; \
		uv run --project ../ppx-align ppx-align build-layout-tree $(OUTPUT)/$$doc; \
	done

align:
	@i=0; \
	for doc in $(DOCS); do \
		gpu=$$((i % $(GPUS))); \
		echo "[GPU $$gpu] align $$doc"; \
		CUDA_VISIBLE_DEVICES=$$gpu uv run --project ../ppx-align ppx-align build $(OUTPUT)/$$doc & \
		i=$$((i+1)); \
	done; \
	wait

corrupt:
	@for doc in $(DOCS); do \
		echo "[corrupt] $$doc"; \
		uv run ppx-bench corrupt $(OUTPUT)/$$doc -n $(NOISE) --seed $(SEED); \
	done

align-noise:
	@i=0; \
	for doc in $(DOCS); do \
		gpu=$$((i % $(GPUS))); \
		echo "[GPU $$gpu] align-noise $$doc ($(NOISE))"; \
		CUDA_VISIBLE_DEVICES=$$gpu uv run --project ../ppx-align ppx-align build $(OUTPUT)/$$doc --noise $(NOISE) & \
		i=$$((i+1)); \
	done; \
	wait

benchmarks:
	uv run ppx-bench benchmark $(OUTPUT)
	uv run ppx-bench noise-benchmark $(OUTPUT)
	uv run ppx-bench precision-recall-benchmark $(OUTPUT)
	uv run ppx-bench summary $(OUTPUT)

summary:
	uv run ppx-bench summary $(OUTPUT)

clean:
	rm -rf $(OUTPUT)
