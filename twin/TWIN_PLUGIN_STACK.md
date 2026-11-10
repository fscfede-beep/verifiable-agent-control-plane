# Twin Plugin Stack v1.4

## Recommended stack

### Core — required
1. Twin Control Plane (repository plugin)
   - canonical verification loop
   - fail-closed promotion
2. Twin Sync (repository plugin)
   - export comparison
   - common TwinSpec candidate

### Shared knowledge — choose one primary
3. Memco Shared Memory
   - candidate for cross-agent shared memory
   - verify privacy, retention, and account/workspace scope before use
4. AI Wisebase
   - candidate for storing chats/files as a private reference layer
   - useful where a shared knowledge base is more appropriate than native account memory

Do not enable two competing memory stores until one is selected as canonical.

### Agent orchestration / evaluation
5. Brainbase MCP
   - candidate for managed agents, evaluations, orchestrations and MCP configuration
   - use only if its provider authorization and workspace scope fit the two environments

### Pre-execution evidence
6. Neura Relay MCP
   - candidate for decision receipts / pre-execution review
   - use as an evidence/approval layer, not as a substitute for Twin Control Plane state validation

### Workflow automation — optional
7. Tallyfy Workflow Automation
   - candidate for persistent business/process workflows

### Documentation — optional
8. Notion
   - candidate for canonical human-readable TwinSpec notes, decisions and runbooks

## Selection rule

Minimum useful stack:
Twin Control Plane + Twin Sync + one shared knowledge layer.

Full stack for a serious deployment:
Twin Control Plane + Twin Sync + one shared knowledge layer + Brainbase MCP + Neura Relay MCP.

Add Tallyfy/Notion only when there is a demonstrated workflow/documentation need.

## Account-twin boundary

Plugins can share reusable skills/workflow logic, but OpenAI's plugin model does not
merge provider accounts or bypass provider authentication. Each account/workspace must
authorize the underlying app separately when required.

## Evidence status

The Plugin Directory currently lists Brainbase MCP, Memco Shared Memory, Neura Relay MCP,
Tallyfy Workflow Automation, Notion, AI Wisebase and WebMCP as available in this environment.
Availability for an individual account can still differ by plan, role, workspace, region and
app permissions.

The plugin dependency resolver could not resolve these display names to current-release
dependency metadata in this environment, so no dependency details are asserted here.

## Acceptance

Before adding any external plugin to both twin environments, record:
- plugin version;
- required apps;
- provider authorization scope;
- allowed actions;
- approval policy;
- data retention/privacy notes;
- environment A result;
- environment B result.

Then run the A/B attestation gate.
