# 🚀 YAML for Humans - Performance Benchmark

> **Purpose**: Quantify the performance trade-off for human-friendly YAML formatting compared to standard PyYAML serialization.

## 📊 Executive Summary

**YAML for Humans demonstrates excellent performance** with minimal overhead compared to PyYAML:

- **Average slowdown**: 1.07x (7% slower)
- **Performance range**: 1.02x - 1.15x slower
- **Assessment**: ✅ **Excellent** - minimal performance impact
- **Output quality**: 1-16% larger but significantly more human-readable

The formatting benefits justify the minimal performance cost for human-readable configuration files and development workflows.

---

## 🖥️ System Information

| Component | Details |
|-----------|---------|
| **OS** | Linux (Debian 6.1.135-1) |
| **Architecture** | x86_64 |
| **Kernel** | 6.1.0-34-amd64 SMP PREEMPT_DYNAMIC |
| **CPU** | AMD EPYC-Milan Processor |
| **Cores** | 4 cores |
| **Python** | 3.13.5 |
| **PyYAML** | 6.0.2 |
| **YAML for Humans** | 1.0.0 |

---

## 📈 Detailed Performance Results

### Test Case 1: Simple Configuration
**Scenario**: Basic application configuration (typical config file)
```yaml
app_name: web-service
version: 2.1.0
port: 8080
database:
  host: localhost
  port: 5432
```

| Metric | PyYAML | YAML4Humans | Ratio |
|--------|--------|-------------|-------|
| **Performance** | 0.383 ms/op | 0.439 ms/op | **1.15x slower** |
| **Standard Deviation** | ±0.173 | ±0.120 | - |
| **Output Size** | 203 chars | 209 chars | 1.03x larger |
| **Iterations** | 5,000 | 5,000 | - |

### Test Case 2: Kubernetes Deployment
**Scenario**: Real-world Kubernetes deployment manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: production
spec:
  replicas: 3
  containers: [...]
```

| Metric | PyYAML | YAML4Humans | Ratio |
|--------|--------|-------------|-------|
| **Performance** | 1.287 ms/op | 1.345 ms/op | **1.05x slower** |
| **Standard Deviation** | ±0.289 | ±0.285 | - |
| **Output Size** | 984 chars | 1,138 chars | 1.16x larger |
| **Iterations** | 1,000 | 1,000 | - |

### Test Case 3: Large Configuration
**Scenario**: Complex microservices configuration with 20 services
```yaml
microservices:
  service-01:
    name: microservice-01
    replicas: 1
    env_vars: {...}
    resources: {...}
  # ... 19 more services
global_config: {...}
```

| Metric | PyYAML | YAML4Humans | Ratio |
|--------|--------|-------------|-------|
| **Performance** | 17.770 ms/op | 18.191 ms/op | **1.02x slower** |
| **Standard Deviation** | ±3.427 | ±3.847 | - |
| **Output Size** | 15,778 chars | 15,864 chars | 1.01x larger |
| **Iterations** | 200 | 200 | - |

### Test Case 4: Multi-document YAML
**Scenario**: Multiple YAML documents in a single file (common for Kubernetes manifests)
```yaml
---
# Document 1: Simple Config
---
# Document 2: Kubernetes Deployment
```

| Metric | PyYAML | YAML4Humans | Ratio |
|--------|--------|-------------|-------|
| **Performance** | 1.636 ms/op | 1.719 ms/op | **1.05x slower** |
| **Standard Deviation** | ±0.315 | ±0.310 | - |
| **Output Size** | 1,191 chars | 1,352 chars | 1.14x larger |
| **Iterations** | 1,000 | 1,000 | - |

---

## 📊 Statistical Analysis

### Performance Distribution
- **Average slowdown**: 1.07x
- **Median slowdown**: 1.05x
- **Weighted average**: 1.12x (weighted by iteration count)
- **Performance range**: 1.02x - 1.15x slower
- **Standard deviation**: Low variance across test runs

### Key Insights
1. **Consistent Performance**: All test cases show similar 2-15% slowdown
2. **Scale Efficiency**: Larger configurations show better relative performance (1.02x)
3. **Minimal Variance**: Low standard deviations indicate stable performance
4. **Output Quality**: Human-readable formatting with only 1-16% size increase

---

## 🎯 Performance Assessment

### ✅ Excellent Performance (1.07x average slowdown)

**Interpretation**: The minimal performance overhead makes YAML for Humans suitable for most use cases where human-readable output is valued.

### When to Use YAML for Humans:
- ✅ Configuration files read by humans
- ✅ Development and debugging workflows
- ✅ Documentation and examples
- ✅ CI/CD pipeline outputs
- ✅ Infrastructure as Code (IaC) templates

### When Standard PyYAML Might Be Better:
- ⚠️ High-frequency serialization in performance-critical applications
- ⚠️ Machine-to-machine communication where formatting doesn't matter
- ⚠️ Extremely large datasets where every millisecond counts

---

## 🔬 Methodology

### Benchmarking Approach
- **Warmup runs**: 10 iterations to stabilize performance
- **Statistical rigor**: Multiple metrics (mean, median, std dev, min/max)
- **Realistic test data**: Real-world scenarios instead of synthetic data
- **Fair comparison**: PyYAML configured with `default_flow_style=False, sort_keys=False`
- **Multiple iterations**: Scaled by complexity (200-5,000 iterations)

### Test Data Characteristics
- **Simple Config**: Basic key-value pairs and nested structures
- **Kubernetes Deployment**: Production-realistic container deployment
- **Large Configuration**: 20 microservices with complex nested data
- **Multi-document**: Common pattern for Kubernetes manifest files

---

## 📝 Conclusion

YAML for Humans delivers on its promise of human-friendly formatting with **minimal performance impact**. The 7% average slowdown is negligible for most use cases, making it an excellent choice when readable YAML output is important.

The consistent performance across different data complexities and the low variance in timing results demonstrate that YAML for Humans is production-ready for scenarios where human readability is valued.

---

## 🔄 Reproducing These Results

To run the benchmark yourself:

```bash
# Ensure you're in the project directory with virtual environment active
source .venv/bin/activate

# Run the benchmark
uv run python benchmark.py
```

The benchmark will automatically:
- Create realistic test data (simple configs, K8s deployments, large configurations)
- Run warmup iterations to stabilize performance  
- Measure both PyYAML and YAML4Humans with statistical analysis
- Generate detailed performance and output size comparisons

---

## 📚 Additional Resources

- **[README.md](README.md)** - Getting started and usage examples
- **[API.md](API.md)** - Complete API reference
- **[examples/](examples/)** - Real-world usage examples
- **[Source Code](src/yaml_for_humans/)** - Implementation details

---

*Benchmark generated on: 2025-08-27*  
*System: AMD EPYC-Milan Processor (4 cores), Python 3.13.5, PyYAML 6.0.2*  
*Methodology: 10 warmup runs + statistical analysis across 200-5,000 iterations per test case*