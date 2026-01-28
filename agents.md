# Memory System Usage Guidelines for AI Agents

You have access to a persistent memory system that maintains continuity across conversations. **Use it proactively** to provide better, context-aware assistance.

## Core Principle

**Memory is not optional** - it's a core capability that distinguishes you from a stateless assistant. Users expect you to remember important information and build on past interactions.

## When to Store Memories

### ALWAYS Store When:

- **User shares personal preferences, goals, or constraints**
  - Examples: "I prefer TypeScript over JavaScript", "We're targeting Python 3.9+", "I like minimal comments"

- **User corrects you or clarifies their context**
  - Examples: "Actually, we use PostgreSQL not MySQL", "That's not how our auth system works"

- **You discover important facts about the codebase, architecture, or patterns**
  - Examples: Code structure, naming conventions, architectural decisions, technology stack

- **Conversations involve decisions, trade-offs, or rationales**
  - Examples: "We chose Redis over Memcached because...", "We're avoiding X pattern due to Y"

- **User explicitly asks you to remember something**
  - Examples: "Remember this for next time", "Save this information", "Keep this in mind"

### Store Immediately After:

- Learning the user's coding style, conventions, or preferences
- Completing significant work (architectural decisions, major bug fixes, refactors)
- User provides project-specific context (tech stack, deployment info, team practices)
- Discovering project constraints (performance requirements, security policies, compliance needs)
- User shares domain knowledge specific to their industry or use case

### What Makes Good Memory Content:

- **Factual and specific**: "User prefers functional programming style with minimal classes"
- **Actionable**: "Project uses JWT tokens stored in httpOnly cookies for auth"
- **Contextual**: "Database migrations run via Alembic; never edit migration files directly"
- **Decision rationale**: "Chose SQLite over PostgreSQL for simpler deployment in edge cases"

### What NOT to Store:

- Temporary information or transient state
- Obvious facts available in documentation
- Entire conversation transcripts (extract key points instead)
- Information that's likely to become outdated quickly
- Sensitive data without explicit user permission

## When to Retrieve Memories

### ALWAYS Retrieve:

- **At the start of EVERY conversation** - Check for relevant context about the user or their projects
  - Query pattern: Broad semantic query about the current user/project/task
  - Example: `memory_retrieve("user preferences project context")`

- **When user references past work**
  - Phrases: "remember", "last time", "previously", "earlier", "you said", "we discussed"

- **Before making architectural recommendations**
  - Check for past decisions and constraints to maintain consistency

- **When starting work on a familiar codebase or project**
  - Retrieve project-specific patterns, conventions, and constraints

- **When user asks "do you remember...?"**
  - This is an explicit request to use memory

### Retrieval Strategy:

1. **Start broad**: Begin conversations with general queries about user/project
2. **Narrow as needed**: If initial results aren't helpful, try topic-specific queries
3. **Use topics**: When you know the domain (e.g., "user_preferences", "project_X_architecture")
4. **Check multiple angles**: Try different query phrasings if first attempt yields no results

### Handling Retrieval Results:

- **Integrate naturally**: Don't announce "I found these memories" - just use the context
- **Validate relevance**: Memory may be outdated; ask for confirmation if uncertain
- **Update when needed**: If information has changed, use `memory_update` instead of storing duplicates

## Memory Hygiene Best Practices

### Topics:

Use **consistent, descriptive topic names**:
- `user_preferences` - Personal preferences, coding style, communication style
- `project_<name>_architecture` - Architectural decisions and patterns
- `project_<name>_constraints` - Requirements, limitations, policies
- `codebase_<name>_patterns` - Code conventions, naming standards
- `domain_knowledge_<field>` - Industry-specific or domain knowledge
- `debugging_<issue>` - Important debugging findings and solutions

### Granularity:

- **One concept per memory item** - Don't store entire conversations
- **Focused and specific** - Each memory should be independently useful
- **Self-contained** - Memory should make sense without conversation context

### Tags:

Add **2-5 relevant tags** for cross-cutting concerns:
- Technology tags: `python`, `react`, `postgresql`, `aws`
- Category tags: `security`, `performance`, `testing`, `deployment`
- Pattern tags: `functional`, `oop`, `async`, `microservices`
- Priority tags: `critical`, `deprecated`, `experimental`

### Updates vs. New Memories:

- **Use `memory_update`** when information changes or evolves
- **Store new memory** when it's genuinely new information
- **Delete outdated memories** if they're no longer relevant (use `memory_delete`)

## Quick Start Pattern for Every Conversation

**At the beginning of EVERY new conversation:**

```
1. Call memory_retrieve with a broad query about the user/task
   Example: memory_retrieve("user preferences current project context")

2. If relevant memories exist:
   - Incorporate them naturally into your understanding
   - Don't announce "I found X memories" unless user asks

3. If no memories exist:
   - This might be a first interaction - be ready to learn and store

4. Throughout the conversation:
   - Store new learnings as they emerge
   - Update changed information
   - Build a richer context for future interactions
```

## Automatic Retrieval Triggers

**Detect these patterns and retrieve memory automatically:**

| User Pattern | Action | Example Query |
|--------------|--------|---------------|
| "Remember when we..." | Retrieve immediately | Query about the specific topic mentioned |
| "Last time you..." | Retrieve immediately | Query about past interactions |
| Mentions specific project name | Retrieve project context | "project_name architecture constraints" |
| Asks about their preferences | Retrieve user preferences | "user preferences style" |
| References past decisions | Retrieve decision context | Topic-specific query |
| New conversation starts | Retrieve general context | "user current_project" |

## Proactive Memory Suggestions

When appropriate, **suggest remembering important information**:

- "Would you like me to remember this preference for future conversations?"
- "Should I store this architectural decision for future reference?"
- "I'll remember this pattern for next time we work on this project."

## Special Keywords

When user says:
- **"Remember this"** → ALWAYS call `memory_store` with the relevant content
- **"Save this to memory"** → ALWAYS call `memory_store`
- **"Don't forget"** → ALWAYS call `memory_store`
- **"For next time"** → ALWAYS call `memory_store`

Even if you're uncertain about the perfect topic or tags, store it. You can update/refine later.

## Memory Tool Reference

### Available Tools:

- `memory_store(content, topic, tags)` - Store new information
- `memory_retrieve(query, max_results, topic, return_type)` - Search for information
- `memory_update(memory_id, content, topic, tags)` - Update existing memory
- `memory_delete(memory_id)` - Remove outdated memory
- `memory_list_topics()` - See all available topics (useful for consistency)
- `memory_status()` - Check system health and statistics
- `memory_summarize(...)` - Generate summaries of stored memories

### Return Types:

When using `memory_retrieve`, you can specify:
- `"full_text"` - Get complete original content (default)
- `"summary"` - Get AI-generated summary (faster, more concise)
- `"both"` - Get both summary and full text

Use `"summary"` for quick context checks; use `"full_text"` when you need exact details.

## Anti-Patterns to Avoid

❌ **Don't wait to be asked** - Be proactive about memory
❌ **Don't store everything** - Be selective and meaningful
❌ **Don't ignore past context** - Always check memory at conversation start
❌ **Don't create duplicate memories** - Search first, update if exists
❌ **Don't use vague topics** - Be specific and consistent
❌ **Don't forget to tag** - Tags enable cross-topic discovery

## Success Metrics

You're using memory well when:
- ✅ Users don't have to repeat themselves across conversations
- ✅ You maintain consistency with past decisions and preferences
- ✅ You build on previous work rather than starting from scratch
- ✅ Users feel understood and that their context is preserved
- ✅ You proactively surface relevant past information

---

**Remember: The memory system is most valuable when used proactively, not just reactively. Make it a habit to check and update memory in every conversation.**
