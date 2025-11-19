"""Tests for the Flipt gRPC client."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from flipt_client.grpc import FliptGrpcClient, GrpcClientOptions
from flipt_client.grpc.flipt.evaluation import evaluation_simple_pb2


class TestGrpcClientOptions:
    """Tests for GrpcClientOptions configuration."""

    def test_default_options(self):
        """Test default configuration options."""
        opts = GrpcClientOptions()
        assert opts.address == "localhost:9000"
        assert opts.namespace_key == "default"
        assert opts.environment_key == "default"
        assert opts.secure is False
        assert opts.client_token is None
        assert opts.ssl_cert_path is None

    def test_custom_options(self):
        """Test custom configuration options."""
        opts = GrpcClientOptions(
            address="flipt.example.com:443",
            namespace_key="production",
            environment_key="prod",
            secure=True,
            client_token="test-token"
        )
        assert opts.address == "flipt.example.com:443"
        assert opts.namespace_key == "production"
        assert opts.environment_key == "prod"
        assert opts.secure is True
        assert opts.client_token == "test-token"


class TestFliptGrpcClient:
    """Tests for FliptGrpcClient."""

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_client_initialization_insecure(self, mock_stub, mock_channel):
        """Test client initialization with insecure channel."""
        opts = GrpcClientOptions(address="localhost:9000")
        client = FliptGrpcClient(opts=opts)

        mock_channel.assert_called_once_with("localhost:9000")
        mock_stub.assert_called_once()
        assert client.opts == opts
        assert client.metadata == []

    @patch('flipt_client.grpc.client.grpc.secure_channel')
    @patch('flipt_client.grpc.client.grpc.ssl_channel_credentials')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_client_initialization_secure(self, mock_stub, mock_ssl_creds, mock_channel):
        """Test client initialization with secure channel."""
        opts = GrpcClientOptions(
            address="flipt.example.com:443",
            secure=True,
            client_token="test-token"
        )
        client = FliptGrpcClient(opts=opts)

        mock_ssl_creds.assert_called_once()
        mock_channel.assert_called_once()
        assert client.metadata == [("authorization", "Bearer test-token")]

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_evaluate_boolean(self, mock_stub_class, mock_channel):
        """Test boolean flag evaluation."""
        # Setup mock
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        mock_response = evaluation_simple_pb2.BooleanEvaluationResponse(
            enabled=True,
            flag_key="test-flag",
            reason=evaluation_simple_pb2.MATCH_EVALUATION_REASON
        )
        mock_stub.Boolean.return_value = mock_response

        # Create client and evaluate
        opts = GrpcClientOptions()
        client = FliptGrpcClient(opts=opts)
        result = client.evaluate_boolean(
            flag_key="test-flag",
            entity_id="user-123",
            context={"region": "us-west"}
        )

        # Verify
        assert result.enabled is True
        assert result.flag_key == "test-flag"
        mock_stub.Boolean.assert_called_once()

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_evaluate_variant(self, mock_stub_class, mock_channel):
        """Test variant flag evaluation."""
        # Setup mock
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        mock_response = evaluation_simple_pb2.VariantEvaluationResponse(
            match=True,
            flag_key="test-variant-flag",
            variant_key="variant-a",
            variant_attachment='{"color": "blue"}'
        )
        mock_stub.Variant.return_value = mock_response

        # Create client and evaluate
        client = FliptGrpcClient()
        result = client.evaluate_variant(
            flag_key="test-variant-flag",
            entity_id="user-456",
            context={"tier": "premium"}
        )

        # Verify
        assert result.match is True
        assert result.flag_key == "test-variant-flag"
        assert result.variant_key == "variant-a"
        mock_stub.Variant.assert_called_once()

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_evaluate_batch(self, mock_stub_class, mock_channel):
        """Test batch evaluation."""
        # Setup mock
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        mock_response = evaluation_simple_pb2.BatchEvaluationResponse(
            request_duration_millis=10.5,
            responses=[
                evaluation_simple_pb2.EvaluationResponse(
                    type=evaluation_simple_pb2.BOOLEAN_EVALUATION_RESPONSE_TYPE,
                    boolean_response=evaluation_simple_pb2.BooleanEvaluationResponse(
                        enabled=True,
                        flag_key="flag-1"
                    )
                )
            ]
        )
        mock_stub.Batch.return_value = mock_response

        # Create client and evaluate
        client = FliptGrpcClient()
        requests = [
            {
                "flag_key": "flag-1",
                "entity_id": "user-789",
                "context": {"test": "true"}
            }
        ]
        result = client.evaluate_batch(requests=requests)

        # Verify
        assert result.request_duration_millis == 10.5
        assert len(result.responses) == 1
        mock_stub.Batch.assert_called_once()

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_context_manager(self, mock_stub_class, mock_channel):
        """Test using client as context manager."""
        mock_channel_instance = Mock()
        mock_channel.return_value = mock_channel_instance

        with FliptGrpcClient() as client:
            assert client is not None

        # Verify channel was closed
        mock_channel_instance.close.assert_called_once()

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_close(self, mock_stub_class, mock_channel):
        """Test explicit close."""
        mock_channel_instance = Mock()
        mock_channel.return_value = mock_channel_instance

        client = FliptGrpcClient()
        client.close()

        mock_channel_instance.close.assert_called_once()
        assert client.channel is None

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_namespace_override(self, mock_stub_class, mock_channel):
        """Test namespace override in evaluation."""
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        mock_response = evaluation_simple_pb2.BooleanEvaluationResponse(
            enabled=True,
            flag_key="test-flag"
        )
        mock_stub.Boolean.return_value = mock_response

        client = FliptGrpcClient(
            opts=GrpcClientOptions(namespace_key="default")
        )

        client.evaluate_boolean(
            flag_key="test-flag",
            entity_id="user-123",
            namespace_key="production"
        )

        # Verify the call was made with overridden namespace
        call_args = mock_stub.Boolean.call_args
        request = call_args[0][0]
        assert request.namespace_key == "production"

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_list_flags(self, mock_stub_class, mock_channel):
        """Test list flags functionality."""
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        # Create mock flags
        mock_flag1 = evaluation_simple_pb2.Flag(
            key="flag-1",
            name="Flag 1",
            description="Test flag 1",
            enabled=True,
            type=evaluation_simple_pb2.BOOLEAN_FLAG_TYPE
        )
        mock_flag2 = evaluation_simple_pb2.Flag(
            key="flag-2",
            name="Flag 2",
            description="Test flag 2",
            enabled=False,
            type=evaluation_simple_pb2.VARIANT_FLAG_TYPE
        )

        mock_response = evaluation_simple_pb2.FlagList(
            flags=[mock_flag1, mock_flag2],
            total_count=2,
            next_page_token=""
        )
        mock_stub.ListFlags.return_value = mock_response

        # Create client and list flags
        client = FliptGrpcClient()
        result = client.list_flags(limit=10)

        # Verify
        assert len(result.flags) == 2
        assert result.total_count == 2
        assert result.flags[0].key == "flag-1"
        assert result.flags[1].key == "flag-2"
        mock_stub.ListFlags.assert_called_once()

    @patch('flipt_client.grpc.client.grpc.insecure_channel')
    @patch('flipt_client.grpc.client.evaluation_simple_pb2_grpc.EvaluationServiceStub')
    def test_list_flags_with_pagination(self, mock_stub_class, mock_channel):
        """Test list flags with pagination."""
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        mock_flag = evaluation_simple_pb2.Flag(
            key="flag-1",
            name="Flag 1",
            enabled=True,
            type=evaluation_simple_pb2.BOOLEAN_FLAG_TYPE
        )

        mock_response = evaluation_simple_pb2.FlagList(
            flags=[mock_flag],
            total_count=100,
            next_page_token="next_page_123"
        )
        mock_stub.ListFlags.return_value = mock_response

        # Create client and list flags
        client = FliptGrpcClient()
        result = client.list_flags(limit=50, page_token="page_token_456")

        # Verify
        assert result.next_page_token == "next_page_123"
        assert result.total_count == 100

        # Verify the request was made with correct parameters
        call_args = mock_stub.ListFlags.call_args
        request = call_args[0][0]
        assert request.limit == 50
        assert request.page_token == "page_token_456"
