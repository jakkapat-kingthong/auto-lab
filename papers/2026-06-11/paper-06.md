# Redesign Mixture-of-Experts Routers with Manifold Power Iteration

> ArXiv | 2026-06-11 | paper 6

Router is the cornerstone component to the Mixture-of-Experts models. Serving as expert proxies, the rows of the router matrix compute their similarity to the MoE inputs to determine which subset of experts is activated. Ideally, each router row is designed to encode the expert matrix into this representative vector, such that its dot-product with token can better reflect token-expert affinity. Ho...

→ [http://arxiv.org/abs/2606.12397v1](http://arxiv.org/abs/2606.12397v1)
