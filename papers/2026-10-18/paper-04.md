# SoftCache: Adaptive Step Size Caching for Diffusion Transformers

> ArXiv | 2026-10-18 | paper 4

Diffusion and flow models generate a sample over iterative steps, each a full pass through a large network, and that pass dominates generation cost. Training-free caching accelerates them by reusing activations from recent evaluations instead of recomputing them. Dynamic caching methods decide when to refresh by accumulating a cheap probe of the network input into a staleness signal and spending a...

→ [http://arxiv.org/abs/2610.22369v1](http://arxiv.org/abs/2610.22369v1)
