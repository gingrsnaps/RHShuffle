"""SERVER ONLY: EmpireDrop production API keys for PRIVATE Git deployments.

Contains user-supplied production credentials. Never serve/import this module
in browser assets, publish the repository, or print credentials in logs.
Rotate the key pair if the repository has ever been public. Environment
variables (EMPIREDROP_PUBLIC_KEY / EMPIREDROP_PRIVATE_KEY) override these.
"""
EMPIREDROP_KEYS = {'empiredrop_private_key': 'sk_prod_fBy8TMvWoU4d3s4B9SYjrjBtV90jTGQVcgRdSvFp', 'empiredrop_public_key': 'pk_prod_fIjbtQOdrbVqL8TrUrghtiHMRHy1yG1r'}
