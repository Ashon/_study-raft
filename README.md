# Raft consensus with async python

## Architecture

```
                           Consensus Modules
                             +---------------+
                        +--- | RaftTCPServer | -----+
                        |    +---------------+      V
+------------------+    |                       +-------+
| RaftStateMachine | <--+                       | Event |
+------------------+    |                       +-------+
                        |    +---------------+      A
                        +--- | RaftActor     | -----+
                        |    +---------------+
                        |
                        |  Subsystems
                        |    +-------------------+
                        +--- | RaftStateReporter |
                             +-------------------+

+-----------+
| DataStore |
+-----------+
```
