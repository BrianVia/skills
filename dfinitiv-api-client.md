# Dfinitiv API Client Generation Skill

You are an expert at creating internal API and EventBridge clients for Dfinitiv services. This skill helps generate the package structure and boilerplate code for exposing typed API clients from Dfinitiv services.

## When to Use This Skill

Use this skill when the user asks to:
- Create a new internal API client package for a Dfinitiv service
- Add API endpoints to an existing service package
- Add EventBridge event publishing capabilities to a service
- Set up the package structure for inter-service communication

## Package Structure

Every Dfinitiv service with an API should have a `package/` folder with this structure:

```
package/
├── package.json          # Package configuration
├── index.ts             # Main export file
├── consts/
│   └── EventSource.ts   # Event source constant
├── endpoints/
│   ├── client.ts        # API client export
│   ├── endpoints.ts     # Endpoint definitions
│   ├── env.ts           # Environment variable name constant
│   └── internalApi.ts   # Internal API configuration for CDK permissions
├── enums/
│   └── EventDetailTypes.ts  # Event type enumerations
├── events/
│   └── client.ts        # EventBridge client export
└── interfaces/
    ├── data/            # Data model interfaces
    ├── event/           # Event payload interfaces
    ├── request/         # API request interfaces
    └── response/        # API response interfaces
```

## File Templates

### 1. endpoints/env.ts

```typescript
export const {serviceName}EnvVarName = "{SERVICE_NAME}_API";
```

Example for mojo-offers:
```typescript
export const mojoOffersEnvVarName = "MOJO_OFFERS_API";
```

### 2. consts/EventSource.ts

```typescript
export const {serviceName}EventSource = "{domain}.{service}";
```

Example:
```typescript
export const mojoOffersEventSource = "mojo.offers";
```

### 3. endpoints/internalApi.ts

```typescript
import { {serviceName}EventSource } from "../consts/EventSource";
import { {serviceName}EnvVarName } from "./env";

export const {serviceName}InternalApi = {
  [{serviceName}EnvVarName]: {serviceName}EventSource,
};
```

### 4. endpoints/endpoints.ts

```typescript
import { defineZodEndpoint } from "@dfinitiv/constructs/lambda/endpoints";
import { z } from "@dfinitiv/constructs/shared/zod";
import { SomeRequestSchema } from "../interfaces/request/SomeRequest";
import { SomeResponseSchema } from "../interfaces/response/SomeResponse";

export const endpoints = {
  getSomething: defineZodEndpoint({
    method: "GET",
    path: "resources/{resourceId}",  // Use curly braces for path params
    userAIEnabled: false,
    schemas: {
      request: z.null(),  // Use z.null() for no request body
      response: SomeResponseSchema,
    },
    description: "Description of what this endpoint does",
  }),

  postSomething: defineZodEndpoint({
    method: "POST",
    path: "resources",
    userAIEnabled: false,
    schemas: {
      request: SomeRequestSchema,
      response: SomeResponseSchema,
    },
    description: "Description of what this endpoint does",
  }),
};
```

### 5. endpoints/client.ts

```typescript
import { createApiClient } from "@dfinitiv/constructs/lambda/endpoints";
import { endpoints } from "./endpoints";
import { {serviceName}EnvVarName } from "./env";

const url = process.env[{serviceName}EnvVarName];
if (!url) {
  throw new Error(`Environment variable ${serviceName}EnvVarName} is not set.`);
}

export const {serviceName}ApiClient = createApiClient({ url, endpoints });
```

### 6. enums/EventDetailTypes.ts

Use dot-notation for event type values:

```typescript
export enum EventDetailTypes {
  ResourceCreated = "resource.created",
  ResourceUpdated = "resource.updated",
  ResourceDeleted = "resource.deleted",
}
```

### 7. events/client.ts

```typescript
import { createEventClient } from "@dfinitiv/constructs/lambda/events";
import { EventDetailTypes } from "../enums/EventDetailTypes";
import { ResourceCreatedSchema } from "../interfaces/event/ResourceCreated";
import { ResourceUpdatedSchema } from "../interfaces/event/ResourceUpdated";

enum EventClientDetailTypes {
  ResourceCreated = EventDetailTypes.ResourceCreated,
  ResourceUpdated = EventDetailTypes.ResourceUpdated,
}

export const {serviceName}EventsClient = createEventClient({
  eventDetailTypes: EventClientDetailTypes,
  events: {
    ResourceCreated: { inputSchema: ResourceCreatedSchema },
    ResourceUpdated: { inputSchema: ResourceUpdatedSchema },
  },
});
```

### 8. index.ts

```typescript
// API Client
export { {serviceName}ApiClient } from "./endpoints/client";
export { endpoints as {serviceName}ApiEndpoints } from "./endpoints/endpoints";
export { {serviceName}EnvVarName } from "./endpoints/env";

// Event Client
export { {serviceName}EventsClient } from "./events/client";

// Constants and Enums
export { {serviceName}EventSource } from "./consts/EventSource";
export { EventDetailTypes as {ServiceName}EventDetailTypes } from "./enums/EventDetailTypes";

// Interfaces
export * from "./interfaces";
```

### 9. package.json

```json
{
  "name": "@dfinitiv/{service-name}",
  "version": "0.1.0",
  "scripts": {},
  "devDependencies": {},
  "dependencies": {},
  "publishConfig": {
    "registry": "https://npm.pkg.github.com/dfinitiv"
  }
}
```

### 10. tsconfig-package.json (at service root)

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "rootDir": "./package",
    "outDir": "./package",
    "declaration": true,
    "emitDeclarationOnly": false
  },
  "include": ["package/**/*"],
  "exclude": ["node_modules", "**/*.test.ts"]
}
```

## Interface/Schema Files

### Request Schema (interfaces/request/SomeRequest.ts)

```typescript
import { z } from "@dfinitiv/constructs/shared/zod";

export const SomeRequestSchema = z.object({
  field1: z.string(),
  field2: z.number().optional(),
});

export type SomeRequest = z.infer<typeof SomeRequestSchema>;
```

### Response Schema (interfaces/response/SomeResponse.ts)

```typescript
import { z } from "@dfinitiv/constructs/shared/zod";

export const SomeResponseSchema = z.object({
  id: z.string(),
  createdAt: z.string().datetime(),
});

export type SomeResponse = z.infer<typeof SomeResponseSchema>;
```

### Event Schema (interfaces/event/ResourceCreated.ts)

```typescript
import { z } from "@dfinitiv/constructs/shared/zod";

export const ResourceCreatedSchema = z.object({
  resourceId: z.string(),
  createdBy: z.string(),
  timestamp: z.string().datetime(),
});

export type ResourceCreated = z.infer<typeof ResourceCreatedSchema>;
```

## Usage in CDK (lib/routes/)

When other services need to call this API, they import the internalApi:

```typescript
import { {serviceName}InternalApi } from "@dfinitiv/{service-name}/endpoints/internalApi";

export const events: EventBridgeLambda[] = [
  {
    entry: "./lambda/event/some-handler.ts",
    internalApis: {
      ...{serviceName}InternalApi,
    },
    // ... other config
  },
];
```

## Key Conventions

1. **Path Parameters**: Always use curly braces `{paramName}` not colons `:paramName`
2. **No Request Body**: Use `z.null()` for GET/DELETE endpoints without a body
3. **Event Types**: Use dot-notation like `"resource.created"`, `"user.updated"`
4. **Environment Variables**: Use SCREAMING_SNAKE_CASE like `MOJO_OFFERS_API`
5. **Naming**: Use camelCase for exports (e.g., `mojoOffersApiClient`)
6. **Schemas**: Use `inputSchema` for event publishing, `schema` for bidirectional

## Existing Services Reference

| Service | Package | Env Var | Event Source |
|---------|---------|---------|--------------|
| mojo-users | @dfinitiv/mojo-users | MOJO_USERS_API | mojo.users |
| mojo-offers | @dfinitiv/mojo-offers | MOJO_OFFERS_API | mojo.offers |
| savvy-geo | @dfinitiv/savvy-geo | SAVVY_GEO_API | savvy.geo |
| savvy-metadata | @dfinitiv/savvy-metadata | SAVVY_METADATA_API | savvy.metadata |

## Workflow

When asked to create or update an API client package:

1. **Identify the service name** and derive naming conventions
2. **Check if package/ folder exists** - create structure if not
3. **Create/update files in order**:
   - env.ts (environment variable)
   - EventSource.ts (event source constant)
   - internalApi.ts (CDK permissions)
   - Request/Response schemas in interfaces/
   - endpoints.ts (endpoint definitions)
   - client.ts (API client export)
   - EventDetailTypes.ts (if events needed)
   - events/client.ts (if events needed)
   - index.ts (main exports)
   - package.json
4. **Add tsconfig-package.json** if not present at service root
5. **Update existing files** rather than creating new ones when possible

## Important Notes

- This is strictly for internal Dfinitiv work
- All services follow the same patterns for consistency
- Use @dfinitiv/constructs helpers (defineZodEndpoint, createApiClient, createEventClient)
- Validate all data with Zod schemas
- Include descriptions for all endpoints
