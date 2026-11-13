# Performance Notes

V12 removes the former five-second community poller, avatar processing, related state serialization, and associated public/Admin payload fields.

Other optimizations:

- Runtime requirements no longer include Pillow.
- Provider-specific scripts load only where needed.
- Repeated operational events are grouped.
- EmpireDrop honors provider cache duration.
- Public responses retain conditional caching and ETags.
- FastDeploy excludes tests, screenshots, caches, and development documentation.
- A single App Platform instance avoids concurrent JSON writers.
