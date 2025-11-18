# Flipt gRPC Client

A Python gRPC client for Flipt server-side feature flag evaluation.

## Overview

This gRPC client allows you to evaluate feature flags by communicating directly with a Flipt server via gRPC. Unlike the main `FliptClient` which performs client-side evaluation using a local FFI engine, this client makes network calls to the Flipt server for each evaluation.

## When to Use

**Use the gRPC client when:**
- You want server-side evaluation for centralized control
- You need real-time flag updates without polling
- You prefer not to bundle the FFI engine with your application
- You're building microservices that can easily communicate with a central Flipt server

**Use the FFI client (FliptClient) when:**
- You need offline evaluation capabilities
- You want to minimize network latency
- You need to evaluate flags in environments without reliable network connectivity
- You want to reduce load on your Flipt server

## Installation

The gRPC dependencies are included with the `flipt-client` package:

```bash
pip install flipt-client
```

## Quick Start

```python
from flipt_client.grpc import FliptGrpcClient, GrpcClientOptions

# Create a client
client = FliptGrpcClient(
    opts=GrpcClientOptions(
        address="localhost:9000",
        namespace_key="default",
        environment_key="production"
    )
)

# Evaluate a boolean flag
result = client.evaluate_boolean(
    flag_key="my-feature",
    entity_id="user-123",
    context={"region": "us-west"}
)

print(f"Feature enabled: {result.enabled}")

# Always close the client
client.close()
```

## Configuration

### GrpcClientOptions

- `address` (str): The address of the Flipt gRPC server (default: "localhost:9000")
- `namespace_key` (str): The namespace to use for evaluations (default: "default")
- `environment_key` (str): The environment to use for evaluations (default: "default")
- `secure` (bool): Whether to use TLS/SSL for the connection (default: False)
- `client_token` (str, optional): Client token for authentication
- `ssl_cert_path` (str, optional): Path to SSL certificate for secure connections

## Usage Examples

### Boolean Flag Evaluation

```python
from flipt_client.grpc import FliptGrpcClient, GrpcClientOptions

client = FliptGrpcClient(opts=GrpcClientOptions(address="localhost:9000"))

result = client.evaluate_boolean(
    flag_key="enable-feature-x",
    entity_id="user-456",
    context={"plan": "premium", "region": "us-east"}
)

print(f"Enabled: {result.enabled}")
print(f"Reason: {result.reason}")
print(f"Duration: {result.request_duration_millis}ms")

client.close()
```

### Variant Flag Evaluation

```python
result = client.evaluate_variant(
    flag_key="color-theme",
    entity_id="user-789",
    context={"device": "mobile"}
)

print(f"Variant: {result.variant_key}")
print(f"Attachment: {result.variant_attachment}")
```

### Batch Evaluation

Evaluate multiple flags in a single request:

```python
batch_requests = [
    {
        "flag_key": "feature-a",
        "entity_id": "user-123",
        "context": {"role": "admin"}
    },
    {
        "flag_key": "feature-b",
        "entity_id": "user-123",
        "context": {"role": "admin"}
    }
]

result = client.evaluate_batch(requests=batch_requests)

for response in result.responses:
    if response.HasField("boolean_response"):
        print(f"Flag: {response.boolean_response.flag_key}, Enabled: {response.boolean_response.enabled}")
    elif response.HasField("variant_response"):
        print(f"Flag: {response.variant_response.flag_key}, Variant: {response.variant_response.variant_key}")
```

### Context Manager

Use the context manager for automatic cleanup:

```python
with FliptGrpcClient(opts=GrpcClientOptions(address="localhost:9000")) as client:
    result = client.evaluate_boolean("my-flag", "user-123")
    print(result.enabled)
# Client is automatically closed
```

### Secure Connection with Authentication

```python
client = FliptGrpcClient(
    opts=GrpcClientOptions(
        address="flipt.example.com:443",
        namespace_key="production",
        secure=True,
        client_token="your-client-token"
    )
)

result = client.evaluate_boolean("secure-flag", "user-secure")
client.close()
```

### Custom SSL Certificate

```python
client = FliptGrpcClient(
    opts=GrpcClientOptions(
        address="flipt.internal:9000",
        secure=True,
        ssl_cert_path="/path/to/ca-cert.pem"
    )
)
```

## Error Handling

The client raises `grpc.RpcError` for gRPC-related errors:

```python
import grpc

try:
    result = client.evaluate_boolean("my-flag", "user-123")
except grpc.RpcError as e:
    print(f"gRPC error: {e.code()}")
    print(f"Details: {e.details()}")
```

## Comparison with FFI Client

| Feature | gRPC Client | FFI Client |
|---------|-------------|------------|
| Evaluation Location | Server-side | Client-side |
| Network Dependency | Required for each call | Only for initial fetch |
| Offline Support | No | Yes (with fallback) |
| Latency | Higher (network calls) | Lower (in-process) |
| Server Load | Higher | Lower |
| Real-time Updates | Immediate | Polling/Streaming |
| Binary Dependencies | None | Platform-specific FFI library |

## Proto File Location

The proto files used to generate this client are located in:
- `proto/flipt/evaluation/evaluation_simple.proto`

## Regenerating gRPC Code

If you need to regenerate the gRPC code from the proto files:

```bash
python -m grpc_tools.protoc \
  -I./proto \
  --python_out=./flipt_client/grpc \
  --grpc_python_out=./flipt_client/grpc \
  proto/flipt/evaluation/evaluation_simple.proto
```

Then fix the import in `evaluation_simple_pb2_grpc.py`:
```python
# Change this:
from flipt.evaluation import evaluation_simple_pb2
# To this:
from . import evaluation_simple_pb2
```

## Server Configuration

Make sure your Flipt server has gRPC enabled. The default gRPC port is 9000.

In your Flipt configuration:

```yaml
server:
  grpc:
    enabled: true
    port: 9000
```

## License

MIT License - see LICENSE file for details.
