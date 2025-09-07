# Performance Benchmarks

## System Information
- **OS**: Linux 6.1.0-34-amd64 (Debian)
- **CPU**: AMD EPYC-Milan Processor
- **Python**: 3.11.11
- **Date**: 2025-09-07

## Benchmark Results

### YAML Serialization Performance
PyYAML vs YAML for Humans comparison with statistical significance testing.

| Test Case | PyYAML (ms/op) | YAML4Humans (ms/op) | Performance | Output Size |
|-----------|----------------|---------------------|-------------|-------------|
| Simple Config | 0.374 ±0.068 | 0.433 ±0.091 | 1.16x slower | 1.03x larger |
| Kubernetes Deployment | 1.319 ±0.261 | 1.376 ±0.247 | Equivalent* | 1.16x larger |
| Large Configuration | 18.217 ±3.682 | 18.265 ±3.729 | Equivalent* | 1.01x larger |
| Multi-document | 1.773 ±0.357 | 1.971 ±0.339 | 1.11x slower | 1.14x larger |

*Within measurement error (10% threshold)

### Performance Summary
- **Average performance ratio**: 1.08x
- **Median performance ratio**: 1.08x  
- **Weighted average ratio**: 1.13x
- **Range**: 1.00x - 1.16x

### Test Case Distribution
- **YAML4Humans faster**: 0 cases
- **YAML4Humans slower**: 2 cases
- **Equivalent performance**: 2 cases

### Overall Assessment
**Excellent** - Performance is essentially equivalent within measurement variability.

## Methodology

### Timing Approach
- 50 warmup iterations to stabilize JIT/caching effects
- Garbage collection control to reduce measurement noise
- Outlier removal (5% trimmed mean) for stability
- Statistical significance threshold of 10% to account for system variability

### Test Data Characteristics
- **Simple Config**: Basic application configuration (5,000 iterations)
- **Kubernetes Deployment**: Complex nested structure (1,000 iterations)
- **Large Configuration**: 20 microservices configuration (200 iterations)
- **Multi-document**: Multiple YAML documents (1,000 iterations)

## Interpretation

YAML for Humans prioritizes human-readable output over raw performance. The corrected benchmark shows:

1. **Performance trade-off**: 8-16% slower in some cases, equivalent in others - reasonable for formatting benefits
2. **Output quality**: Consistently more readable with minimal size overhead (1-16% larger)
3. **Statistical significance**: Results within 10% considered equivalent due to measurement variability
4. **Realistic results**: No false claims of superiority over PyYAML

Performance differences are primarily due to additional formatting logic rather than algorithmic inefficiency. For configuration files and development workflows where readability matters, this trade-off is typically acceptable.

## Notes

- **Methodology fixes**: Eliminated StringIO overhead, lambda capture bugs, and statistical significance issues
- **Fair comparison**: Both libraries now use equivalent string output methods
- **Realistic thresholds**: 10% significance threshold prevents false performance claims
- Results may vary based on system load, Python implementation, and data characteristics  
- Any claims of superior performance should be viewed skeptically and verified independently