- thesis
  - what neural network architectures are used for paddleocr?
  - have a formal data modeling of the output of paddleocr.
    - text segment and word identification
    - layout analysis
  - our framework:
    - visual tokens (VT) (produced by paddleocr), hierarchical organization
    - text tokens (TT) (produced by markdown extraction)
  - alignment problem:
    - define the alignment function as: visual tokens to source spans
    - constraints:
      - alignment must respect reading order, and parent-child relation in layout tree
    - quality of alignment: scoring function based total similarity between VT and TT.
    - algorithms:
      - DP formulation: O(nL^2) where n = |VT|, L = |TT|.  Guarantees optimal solution.
      - GREEDY: O(nL)
      - Hybrid: if L < c, use DP, else use GREEDY.
    - future work:
      - evaluation



# Thesis plan

## Abstract
## 1. Introduction

- What is the problem we are trying to solve? Why is it a problem? Where is the gap in knowledge? Who has worked on this problem? When did this problem surface? How do we propose to solve it? What technologies will we use to solve it?

## 2. Overview of PaddlePaddle (PaddleOCRv5 and PPDocLayout v3)

- What neural network architectures are used for paddleocr?
- Formal data modeling output of paddleocr
- Text, segment, and word identification
- Layout analysis

## 3. Proposed Framework

- Define the framework. Data structures and pipeline.
- Visual Tokens (VT) (produced by paddleocr), hierarchical organization
- Text Tokens (TT) (produced by markdown extraction)
- Layout Tree

## 4. Alignment Problem
- Formal definition
    - Define the alignment function as: Visual Tokens (VT) to Text Token (TT) source spans
- Constraints:
    - Alignment must respect reading order, and parent-child relation in layout tree
- Quality of alignment: scoring function based total similarity between VT and TT.
- Algorithms:
    - DP formulation: O(nL^2) where n = |VT|, L = |TT|.  Guarantees optimal solution.
    - GREEDY: O(nL)
    - Hybrid: if L < c, use DP, else use GREEDY.
## 5. Future Work
- Evaluation