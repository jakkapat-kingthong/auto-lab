# Sign compression for Muon: SignMuon, MuonSign, and the Limits of Error Feedback

> ArXiv | 2026-08-03 | paper 5

SignMuon compresses the Muon update to one bit per parameter by taking its elementwise sign, providing the most direct way to run a matrix-aware optimizer under an extremely low communication budget. It outperforms SignSGD in practice, yet it can ascend even on a linear function. Signing the gradient before the Linear Minimization Oracle (LMO), rather than after, does not repair this: we construct...

→ [http://arxiv.org/abs/2607.29674v1](http://arxiv.org/abs/2607.29674v1)
