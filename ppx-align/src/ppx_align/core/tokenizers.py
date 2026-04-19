from __future__ import annotations
from abc import ABC, abstractmethod


class PPXTokenizer(ABC):
    @abstractmethod
    def tokenize(self, text: str) -> list[tuple[int, int]]:
        """Return character-offset spans for each token in text."""
        ...


class TreebankTokenizer(PPXTokenizer):
    def __init__(self):
        import nltk
        from nltk.tokenize import TreebankWordTokenizer
        nltk.download("punkt", quiet=True)
        nltk.download("punkt_tab", quiet=True)
        self._tok = TreebankWordTokenizer()

    def tokenize(self, text: str) -> list[tuple[int, int]]:
        return list(self._tok.span_tokenize(text))


class PretrainedAutoTokenizer(PPXTokenizer):
    def __init__(self, model_name: str):
        from transformers import AutoTokenizer
        self._tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)

    def tokenize(self, text: str) -> list[tuple[int, int]]:
        encoded = self._tok(text, return_offsets_mapping=True, add_special_tokens=False)
        return list(encoded["offset_mapping"])
