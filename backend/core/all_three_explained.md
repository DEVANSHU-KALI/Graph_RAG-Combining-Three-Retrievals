
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

