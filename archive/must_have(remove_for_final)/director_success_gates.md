# Director Success Gates

This document defines the success gates for evaluating the model director.

## Routing Accuracy
- **Metric:** Percentage of requests routed to the correct model based on a manually curated test set.
- **Target:** > 95%

## Latency
- **Metric:** Average and p95 latency for director-guided calls compared to direct calls.
- **Target:** Director overhead should be < 200ms on average.

## Uptime
- **Metric:** Percentage of time the director service is available.
- **Target:** > 99.9%
