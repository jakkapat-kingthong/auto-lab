# FVAttn: Adaptive Sparse Attention with Runtime Load Balancing for Video Generation

> ArXiv | 2026-07-20 | paper 3

Video Diffusion Transformers process long spatio-temporal sequences, making self-attention the main bottleneck in high-resolution video generation. Training-free sparse attention reduces this cost, but adaptive Top-$p$ routing creates uneven per-head workloads under multi-GPU sequence parallelism. The resulting workload heterogeneity turns sparse attention into a rank-level straggler problem. We p...

→ [http://arxiv.org/abs/2607.16190v1](http://arxiv.org/abs/2607.16190v1)
