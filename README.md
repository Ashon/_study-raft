# Raft consensus with async python

## Architecture

```
                            +---------------+
                       +--> | RaftTCPServer | <----+
                       |    +---------------+      |
+------------------+   |                       +---+---+
| RaftStateMachine |<--+                       | Event |
+------------------+   |                       +---+---+
                       |    +---------------+      |
                       +--> | RaftActor     | <----+
                       |    +---------------+
                       |
                       |    +-------------------+
                       +--> | RaftStateReporter |
                            +-------------------+
```
