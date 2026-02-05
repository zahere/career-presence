# Technical Interview Questions

> Organized by category with AgentiCraft-relevant answers

---

## System Design

### Q1: "Design a multi-agent orchestration system"

**Clarifying Questions:**
- How many concurrent agents?
- What's the latency requirement?
- Do agents need to communicate with each other?
- What's the failure mode tolerance?

**High-Level Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                          │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Orchestration Layer                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   Router    │ │  Scheduler  │ │   Monitor   │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Agent Pool                              │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐              │
│  │Agent 1│ │Agent 2│ │Agent 3│ │Agent N│              │
│  └───────┘ └───────┘ └───────┘ └───────┘              │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              LLM Provider Layer                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ OpenAI  │ │Anthropic│ │ Cohere  │ │  Local  │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
└─────────────────────────────────────────────────────────┘
```

**Key Components (from AgentiCraft experience):**
1. **Service Mesh** - 27 services with intelligent routing
2. **Pattern Library** - 116 composable patterns
3. **Resilience Layer** - Circuit breakers, retries, fallbacks
4. **Coordination Protocol** - A2A for agent-to-agent, MCP for tools

**Scaling Considerations:**
- Horizontal scaling of agent pool
- Connection pooling to LLM providers
- Caching for repeated queries
- Rate limiting per provider

**From My Experience:**
> "In AgentiCraft, we achieved <150ms p99 latency with 100+ concurrent agents by implementing intelligent provider routing that reduced costs by 32% while maintaining 99.2% task success rate."

---

### Q2: "Design a RAG system for enterprise documents"

**Key Components:**
1. **Ingestion Pipeline**
   - Document parsing (PDF, DOCX, HTML)
   - Chunking strategy (semantic vs fixed-size)
   - Embedding generation
   
2. **Vector Store**
   - Qdrant, Pinecone, Weaviate
   - Hybrid search (dense + sparse)
   
3. **Retrieval Layer**
   - Query expansion
   - Re-ranking
   - Hierarchical retrieval
   
4. **Generation Layer**
   - Context assembly
   - Prompt engineering
   - Response validation

**From Smoove Experience:**
> "At Smoove, we built a RAG pipeline that processed 50+ source documents, using semantic chunking and hierarchical retrieval. We achieved 98.9% time reduction while improving content quality 3.2x."

**Evaluation:**
- Relevance scoring
- Faithfulness checking
- LLM-as-judge for quality

---

### Q3: "How would you reduce LLM inference costs?"

**Strategies (implemented in AgentiCraft):**

1. **Intelligent Routing**
   - Route simple queries to cheaper/faster models
   - Reserve expensive models for complex tasks
   - Result: 32% cost reduction

2. **Caching**
   - Semantic caching for similar queries
   - Exact match caching for repeated queries
   
3. **Batching**
   - Group requests where latency allows
   - Reduces per-request overhead

4. **Prompt Optimization**
   - Shorter prompts = fewer tokens
   - Template reuse
   - Context compression

5. **Token Management**
   - Track token usage per request
   - Budget allocation per agent
   - Alert on anomalies

---

## Coding Questions

### Common Patterns to Know

**1. Rate Limiter**
```python
from collections import deque
import time

class RateLimiter:
    def __init__(self, max_calls: int, window_seconds: int):
        self.max_calls = max_calls
        self.window = window_seconds
        self.calls = deque()
    
    def allow(self) -> bool:
        now = time.time()
        # Remove old calls
        while self.calls and self.calls[0] < now - self.window:
            self.calls.popleft()
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
```

**2. Circuit Breaker**
```python
from enum import Enum
from datetime import datetime, timedelta

class State(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = State.CLOSED
        self.last_failure_time = None
    
    def call(self, func, *args, **kwargs):
        if self.state == State.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = State.HALF_OPEN
            else:
                raise Exception("Circuit is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failures = 0
        self.state = State.CLOSED
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = State.OPEN
```

**3. LRU Cache**
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()
    
    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```

---

## LLM/ML Questions

### Q: "How do you evaluate LLM outputs?"

**Framework (from Smoove experience):**

1. **Automated Metrics**
   - Relevance scoring (embedding similarity)
   - Coherence checking
   - Factual accuracy vs source

2. **LLM-as-Judge**
   - Use a more capable model to evaluate
   - Define clear rubrics
   - Multiple evaluation passes

3. **Human Evaluation**
   - A/B testing with real users
   - Expert review for domain-specific content

4. **Continuous Monitoring**
   - Drift detection
   - Quality regression alerts
   - User feedback integration

---

### Q: "Explain the transformer architecture"

**Key Points:**
- Self-attention mechanism
- Query, Key, Value matrices
- Multi-head attention
- Positional encoding
- Feed-forward networks
- Layer normalization

**Be ready to explain:**
- Why attention over RNNs
- Computational complexity (O(n²))
- KV caching for inference
- Context window limitations

---

### Q: "What are the challenges of multi-agent systems?"

**From AgentiCraft Experience:**

1. **Coordination Overhead**
   - Agents communicating = more tokens
   - Solution: Efficient protocols (A2A, MCP)
   - Result: 45% reduction in redundant calls

2. **State Management**
   - Distributed state is hard
   - Solution: Event-driven architecture, message passing

3. **Failure Cascades**
   - One agent failing affects others
   - Solution: Circuit breakers, isolation, fallbacks

4. **Scaling**
   - Non-linear complexity growth
   - My research: Structured decoding fails at n=50
   - Solution: Mesh-native coordination

5. **Debugging**
   - Hard to trace multi-agent flows
   - Solution: Distributed tracing (OpenTelemetry)

---

## Infrastructure Questions

### Q: "How do you handle high availability for ML services?"

**Strategies:**
1. **Redundancy** - Multiple instances across zones
2. **Load Balancing** - Distribute requests evenly
3. **Health Checks** - Automatic unhealthy instance removal
4. **Graceful Degradation** - Fallback to simpler models
5. **Circuit Breakers** - Prevent cascade failures

**From AgentiCraft:**
> "We designed for 99.9% uptime with automatic failover across 10+ LLM providers. If OpenAI is slow, we route to Anthropic. If cloud is down, we fall back to local models."

---

### Q: "Explain your CI/CD process"

**From Visual Arena:**
```
Code Push → Lint/Test → Build → Security Scan → 
Deploy to Staging → Integration Tests → 
Manual Approval → Production Deploy
```

- GitHub Actions for automation
- ArgoCD for Kubernetes deployments
- <2-minute deployment cycles
- Automatic rollback on failures

---

## Questions to Ask Back

**For Technical Interviews:**
1. "What's the most challenging technical problem the team has solved recently?"
2. "How do you handle technical debt?"
3. "What's your testing strategy for ML systems?"

**For System Design:**
1. "Are there any constraints I should consider?"
2. "What's the expected scale?"
3. "What's the latency budget?"
