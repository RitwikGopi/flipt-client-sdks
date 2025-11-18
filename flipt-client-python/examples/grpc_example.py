"""
Example usage of the Flipt gRPC client for server-side evaluation.

This example demonstrates how to use the FliptGrpcClient to evaluate
flags using gRPC communication with a Flipt server.
"""

from flipt_client.grpc import FliptGrpcClient, GrpcClientOptions


def main():
    """Main example function demonstrating various gRPC client features."""

    # Example 1: Basic usage with default settings
    print("=" * 60)
    print("Example 1: Basic boolean flag evaluation")
    print("=" * 60)

    client = FliptGrpcClient(
        opts=GrpcClientOptions(
            address="localhost:9000",
            namespace_key="default",
            environment_key="default"
        )
    )

    try:
        result = client.evaluate_boolean(
            flag_key="my-boolean-flag",
            entity_id="user-123",
            context={"region": "us-west", "plan": "premium"}
        )

        print(f"Flag: {result.flag_key}")
        print(f"Enabled: {result.enabled}")
        print(f"Reason: {result.reason}")
        print(f"Duration: {result.request_duration_millis}ms")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

    # Example 2: Variant flag evaluation
    print("\n" + "=" * 60)
    print("Example 2: Variant flag evaluation")
    print("=" * 60)

    client = FliptGrpcClient(
        opts=GrpcClientOptions(
            address="localhost:9000",
            namespace_key="default",
            environment_key="production"
        )
    )

    try:
        result = client.evaluate_variant(
            flag_key="my-variant-flag",
            entity_id="user-456",
            context={"country": "US", "tier": "gold"}
        )

        print(f"Flag: {result.flag_key}")
        print(f"Match: {result.match}")
        print(f"Variant Key: {result.variant_key}")
        print(f"Variant Attachment: {result.variant_attachment}")
        print(f"Reason: {result.reason}")
        print(f"Segments: {result.segment_keys}")
        print(f"Duration: {result.request_duration_millis}ms")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

    # Example 3: Batch evaluation
    print("\n" + "=" * 60)
    print("Example 3: Batch evaluation")
    print("=" * 60)

    client = FliptGrpcClient(
        opts=GrpcClientOptions(
            address="localhost:9000",
            namespace_key="default"
        )
    )

    try:
        batch_requests = [
            {
                "flag_key": "feature-a",
                "entity_id": "user-789",
                "context": {"region": "eu-west"}
            },
            {
                "flag_key": "feature-b",
                "entity_id": "user-789",
                "context": {"plan": "enterprise"}
            },
            {
                "flag_key": "feature-c",
                "entity_id": "user-789",
                "context": {"beta_user": "true"}
            }
        ]

        result = client.evaluate_batch(requests=batch_requests)

        print(f"Total duration: {result.request_duration_millis}ms")
        print(f"Number of evaluations: {len(result.responses)}")

        for i, response in enumerate(result.responses):
            print(f"\nEvaluation {i + 1}:")
            print(f"  Type: {response.type}")

            if response.HasField("boolean_response"):
                print(f"  Boolean Result:")
                print(f"    Flag: {response.boolean_response.flag_key}")
                print(f"    Enabled: {response.boolean_response.enabled}")
            elif response.HasField("variant_response"):
                print(f"  Variant Result:")
                print(f"    Flag: {response.variant_response.flag_key}")
                print(f"    Variant: {response.variant_response.variant_key}")
            elif response.HasField("error_response"):
                print(f"  Error:")
                print(f"    Flag: {response.error_response.flag_key}")
                print(f"    Reason: {response.error_response.reason}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

    # Example 4: Using context manager for automatic cleanup
    print("\n" + "=" * 60)
    print("Example 4: Using context manager")
    print("=" * 60)

    with FliptGrpcClient(opts=GrpcClientOptions(address="localhost:9000")) as client:
        try:
            result = client.evaluate_boolean(
                flag_key="simple-flag",
                entity_id="user-999",
                context={"test": "true"}
            )
            print(f"Flag enabled: {result.enabled}")
        except Exception as e:
            print(f"Error: {e}")
    # Client is automatically closed when exiting the context

    # Example 5: Secure connection with TLS
    print("\n" + "=" * 60)
    print("Example 5: Secure connection with authentication")
    print("=" * 60)

    client = FliptGrpcClient(
        opts=GrpcClientOptions(
            address="flipt.example.com:443",
            namespace_key="production",
            secure=True,
            client_token="your-client-token-here",
            # ssl_cert_path="/path/to/cert.pem"  # Optional custom certificate
        )
    )

    try:
        result = client.evaluate_boolean(
            flag_key="secure-flag",
            entity_id="user-secure",
            context={"environment": "production"}
        )
        print(f"Secure evaluation result: {result.enabled}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
