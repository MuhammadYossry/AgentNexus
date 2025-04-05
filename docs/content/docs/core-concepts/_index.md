---
title: "Core Concepts"
description: "Detailed exploration of the fundamental concepts in AgentNexus"
lead: "Understand the building blocks that make up the AgentNexus framework and how they work together."
date: 2025-03-25T08:00:00+00:00
lastmod: 2025-03-25T08:00:00+00:00
draft: false
images: []
weight: 300
---

# Core Concepts

The AgentNexus framework is built around several key concepts that work together to create powerful AI/LLM agents. This section explores these concepts in depth, helping you understand the foundation of the framework.

## What's in this section

{{< cards >}}
  {{< card link="agents" title="Agents" icon="user-circle" subtitle="Definition, configuration, and capabilities" >}}
  {{< card link="actions" title="Actions" icon="user-circle" subtitle="Creating and registering agent actions" >}}
  {{< card link="workflows" title="Workflows" icon="user-circle" subtitle="Building multi-step processes" >}}
  {{< card link="ui-components" title="UI Components" icon="user-circle" subtitle="Overview of UI component system" >}}
  {{< card link="core-concepts/event-handling" title="Event Handling" icon="bell" subtitle="How the event dispatch system works" >}}
  {{< card link="context-management" title="Context Management" icon="variable" subtitle="Preserving state between interactions" >}}
{{< /cards >}}

## How These Concepts Work Together

AgentNexus follows a modular architecture where these core components interact:

1. **Agents** define the capabilities and metadata for AI assistants
2. **Actions** specify what the agents can do and how they behave
3. **Workflows** organize actions into coherent multi-step processes
4. **UI Components** provide interactive interfaces for workflows and actions
5. **Event Handling** manages user interactions with UI components
6. **Context Management** preserves state across workflow steps and sessions

Understanding these concepts and their relationships is essential for effective agent development with AgentNexus.

## Next Steps

<div class="row">
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">
          <a href="agents">Agents →</a>
        </h5>
        <p class="card-text">
          Start by learning about agent definition and configuration.
        </p>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card h-100">
      <div class="card-body">
        <h5 class="card-title">
          <a href="../getting-started/quick-start">Back to Quick Start →</a>
        </h5>
        <p class="card-text">
          Return to the quick start guide for practical examples.
        </p>
      </div>
    </div>
  </div>
</div>