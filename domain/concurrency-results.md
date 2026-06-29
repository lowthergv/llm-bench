# Concurrency benchmark — gemma4:e4b

Fixed notes, same prompt every request. 3 rounds per concurrency level.
Bail condition: p50 > 3× baseline. Warm-up run excluded.

| Concurrent | p50 | p95 | max | Throughput (notes/min) | vs baseline |
|---|---|---|---|---|---|
| 1 | 2.2s | 2.5s | 2.5s | 26.9 | 1.00× |
| 2 | 2.6s | 4.9s | 4.9s | 46.2 | 1.17× |
| 3 | 4.4s | 6.7s | 6.7s | 41.3 | 1.96× |
| 4 | 4.9s | 9.4s | 9.4s | 48.5 | 2.22× |
| 5 | 7.0s | 11.5s | 11.5s | 42.7 | 3.15× |

## Notes

- p50/p95/max are across all 3 rounds combined (3 samples per row).
- Throughput is notes completed per minute of wall-clock time (estimated from p50).
- Ollama queues requests — latency climbs once concurrency exceeds available GPU layers.
