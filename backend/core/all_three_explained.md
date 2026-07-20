
## Configuration Files (`config.py`)

### What is a Configuration File?

A **Configuration File** is a centralized place where an application stores values that control its behavior instead of hardcoding them into the source code.

Common examples include:

- API keys
- Database credentials
- Server settings
- Logging configuration
- AI model names
- Feature flags

---

### Why Do Developers Use It?

- Keeps configuration separate from business logic.
- Makes changing environments (Development, Testing, Production) easy.
- Improves security by keeping secrets outside the source code.
- Provides a **Single Source of Truth** for all configurable values.
- Makes the project easier to maintain.

---

### Is This Enough for Our Project?

**Yes.**

For this project, having a simple configuration file that manages environment variables and application settings is more than enough. It follows the same idea used in production projects, just on a smaller scale.

> **Note:** Production systems often have much larger configuration files containing settings for databases, authentication, logging, caching, monitoring, cloud services, feature flags, and more. Those topics are beyond the scope of this project. If you're interested in advanced configuration management, it's recommended to explore production configuration patterns and tools separately after becoming comfortable with the basics.

---

## Logging File (`logging.py`)
### What is a Logging File?
A **Logging File** (or logging module) sets up a system to record events, status messages, warnings, and errors that happen while an application is running, instead of relying on temporary `print()` statements.
Common uses include:
- Tracking API requests and database queries
- Recording system errors and stack traces
- Monitoring performance and execution times
- Providing runtime visibility without stopping the app
---
### Why Do Developers Use It?
- **Persistence & Organization:** `print()` statements get lost in console spam, whereas loggers can format messages cleanly and write them to log files.
- **Severity Levels:** Allows developers to categorize messages by importance (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- **Formatting & Metadata:** Automatically attaches timestamps, log levels, logger names, and line numbers to every message.
- **Production Debugging:** When an app crashes on a remote server, logs are often the only way to inspect what went wrong.

---
### How is it Implemented in Our Project?
In `backend/core/logging.py`, we set up a centralized logger named `HybridGraphRAG`:
- **Logger Level:** Set to `INFO`, meaning it records standard operational messages, warnings, and errors.
- **Console Handler:** Routes log output to the terminal/console (`StreamHandler`).
- **Custom Formatter:** Formats every line as:
  `YYYY-MM-DD HH:MM:SS | LEVEL | HybridGraphRAG | Message`
- **Propagation Guard:** Sets `logger.propagate = False` and checks `if not logger.handlers:` to prevent duplicate log messages in the console.
---
### Is This Enough for Our Project?
**Yes.**