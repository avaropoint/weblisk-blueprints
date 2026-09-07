# Unbound bindings

`weblisk validate` reports **86 bindings whose target blueprint does not declare
what they bind** — 80 types and 6 behaviours. Every one is
accounted for below.

A binding is what generation reads to know a thing exists. An unbound one means the
model is asked to produce something with no definition, so it invents one — and
nothing about that is visible in the generated code afterwards.

Split by whether the target declares something with a very similar name. **Nothing
here has been changed.** Binding a contract to the wrong type is worse than an honest
fault, so each rename needs confirming by somebody who knows what was meant.

## Types — probably a rename (23)

| Binder | Binds | From | Target declares |
|---|---|---|---|
| `agents/hub.md` | `FederatedListing` | `protocol/federation` | `FederatedTaskResult`, `FederatedTaskRequest` |
| `agents/hub.md` | `KeyRotationAnnouncement` | `protocol/identity` | `KeyRotationRequest` |
| `agents/hub.md` | `PeerRequest` | `protocol/federation` | `FederatedTaskRequest` |
| `agents/lifecycle.md` | `WorkflowResult` | `protocol/types` | `WorkflowExecution`, `WorkflowPhase` |
| `agents/workflow.md` | `WorkflowResult` | `protocol/types` | `WorkflowExecution`, `WorkflowPhase` |
| `architecture/observability.md` | `AuditEntry` | `architecture/orchestrator` | `AgentEntry` |
| `architecture/threat-model.md` | `PeerRequest` | `protocol/federation` | `FederatedTaskRequest` |
| `patterns/api-ai.md` | `GatewayRoute` | `architecture/gateway` | `GatewayConfig` |
| `patterns/api-ai.md` | `Message` | `protocol/types` | `AgentMessage` |
| `patterns/auth-session.md` | `GatewayRoute` | `architecture/gateway` | `GatewayConfig` |
| `patterns/auth-token.md` | `GatewayRoute` | `architecture/gateway` | `GatewayConfig` |
| `patterns/command.md` | `SecretRef` | `patterns/secrets` | `SecretMetadata` |
| `patterns/development.md` | `HealthResponse` | `patterns/observability` | `Response` |
| `patterns/domain-controller.md` | `WLT` | `protocol/identity` | `WLToken` |
| `patterns/expression.md` | `TypeDefinition` | `protocol/types` | `WorkflowDefinition` |
| `patterns/principal-identity.md` | `KeyPair` | `protocol/identity` | `SigningKeyPair`, `Ed25519KeyPair` |
| `patterns/principal-identity.md` | `Token` | `protocol/identity` | `WLToken` |
| `patterns/realtime-chat.md` | `ChatMessage` | `protocol/types` | `AgentMessage` |
| `patterns/storage.md` | `TypeDefinition` | `protocol/types` | `WorkflowDefinition` |
| `patterns/user-management.md` | `PaginatedResponse` | `protocol/types` | `RegisterResponse` |
| `patterns/user-management.md` | `RouteConfig` | `architecture/gateway` | `GatewayConfig`, `Route` |
| `patterns/user-management.md` | `TypeDefinition` | `protocol/types` | `WorkflowDefinition` |
| `patterns/webhook.md` | `TypeDefinition` | `protocol/types` | `WorkflowDefinition` |

## Types — needs authoring (57)

The target declares nothing resembling these. Each is either a type that should exist
and does not, or a binding that should not be there.

| Binder | Binds | From |
|---|---|---|
| `agents/hub.md` | `BehavioralChange` | `architecture/hub` |
| `agents/hub.md` | `CollaboratorInfo` | `architecture/hub` |
| `agents/hub.md` | `MetricsInfo` | `architecture/hub` |
| `agents/hub.md` | `ProviderInfo` | `architecture/hub` |
| `agents/hub.md` | `SearchQuery` | `architecture/hub` |
| `agents/hub.md` | `SearchResult` | `architecture/hub` |
| `agents/incident-response.md` | `AlertEvent` | `protocol/types` |
| `architecture/admin.md` | `Strategy` | `architecture/lifecycle` |
| `architecture/admin.md` | `ThreatBoundary` | `architecture/threat-model` |
| `architecture/admin.md` | `WLS` | `architecture/client` |
| `architecture/admin.md` | `WLT` | `protocol/types` |
| `architecture/change-management.md` | `Strategy` | `architecture/lifecycle` |
| `architecture/cli.md` | `OperatorRecord` | `architecture/admin` |
| `architecture/cli.md` | `WLT` | `protocol/types` |
| `architecture/content.md` | `ViolationRecord` | `architecture/enforcement` |
| `architecture/data-security.md` | `AuditEntry` | `architecture/observability` |
| `architecture/data-security.md` | `FederationPeer` | `protocol/federation` |
| `architecture/enforcement.md` | `ServiceDirectory` | `architecture/orchestrator` |
| `architecture/generation.md` | `protocol-types` | `protocol/types` |
| `architecture/observability.md` | `HealthStatus` | `architecture/agent` |
| `architecture/observability.md` | `ServiceDirectory` | `architecture/orchestrator` |
| `architecture/threat-model.md` | `AuditEntry` | `architecture/observability` |
| `architecture/threat-model.md` | `DataContract` | `patterns/contract` |
| `architecture/threat-model.md` | `EnforcementDecision` | `architecture/enforcement` |
| `architecture/threat-model.md` | `OperatorAuth` | `architecture/admin` |
| `architecture/threat-model.md` | `QuarantineOrder` | `architecture/enforcement` |
| `architecture/threat-model.md` | `SessionToken` | `architecture/gateway` |
| `architecture/threat-model.md` | `StructuredLog` | `architecture/observability` |
| `patterns/api-ai.md` | `AgentManifest` | `architecture/agent` |
| `patterns/api-ai.md` | `Usage` | `protocol/types` |
| `patterns/api-rest.md` | `FieldType` | `protocol/types` |
| `patterns/auth-session.md` | `FieldType` | `protocol/types` |
| `patterns/auth-session.md` | `Identity` | `protocol/identity` |
| `patterns/auth-token.md` | `FieldType` | `protocol/types` |
| `patterns/auth-token.md` | `Identity` | `protocol/identity` |
| `patterns/command.md` | `AgentManifest` | `architecture/agent` |
| `patterns/command.md` | `FieldType` | `protocol/types` |
| `patterns/deployment.md` | `HealthStatus` | `architecture/orchestrator` |
| `patterns/deployment.md` | `OrchestratorConfig` | `architecture/orchestrator` |
| `patterns/domain-controller.md` | `Feedback` | `architecture/lifecycle` |
| `patterns/domain-controller.md` | `Identity` | `protocol/identity` |
| `patterns/domain-controller.md` | `MetricDefinition` | `patterns/observability` |
| `patterns/domain-controller.md` | `Observation` | `architecture/lifecycle` |
| `patterns/domain-controller.md` | `TaskPayload` | `protocol/types` |
| `patterns/file-upload.md` | `AuthToken` | `patterns/auth-token` |
| `patterns/file-upload.md` | `FileRecord` | `protocol/types` |
| `patterns/incident-response.md` | `AlertEvent` | `protocol/types` |
| `patterns/logging.md` | `AgentManifest` | `architecture/agent` |
| `patterns/rate-limiting.md` | `RateLimitConfig` | `protocol/types` |
| `patterns/realtime-chat.md` | `WebSocketFrame` | `protocol/types` |
| `patterns/secrets.md` | `AgentIdentity` | `protocol/identity` |
| `patterns/secrets.md` | `StoreInterface` | `architecture/storage` |
| `platforms/cloudflare.md` | `Identity` | `protocol/identity` |
| `platforms/go.md` | `Identity` | `protocol/identity` |
| `platforms/node.md` | `Identity` | `protocol/identity` |
| `platforms/rust.md` | `Identity` | `protocol/identity` |
| `protocol/federation.md` | `HubManifest` | `architecture/hub` |

## Behaviours — probably a rename (4)

| Binder | Binds | From | Target declares |
|---|---|---|---|
| `patterns/content-identity.md` | `version-declaration` | `patterns/versioning` | `version-migration`, `zero-downtime-transition` |
| `patterns/governance.md` | `event-routing` | `patterns/messaging` | `event-publishing`, `event-subscribing` |
| `patterns/migration.md` | `approval-request` | `patterns/approval` | `approval-routing`, `approval-decision` |
| `patterns/migration.md` | `multi-party-approval` | `patterns/approval` | `multi_party_position` |

## Behaviours — needs authoring (2)

| Binder | Binds | From |
|---|---|---|
| `architecture/generation.md` | `conformance-suite` | `architecture/testing` |
| `architecture/threat-model.md` | `boundary-enforcement` | `architecture/enforcement` |

---

86 of 86 faults are listed above.
