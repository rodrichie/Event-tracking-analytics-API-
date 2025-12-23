# Database Models Architecture

## TimescaleModel vs SQLModel - When to Use Each

### TimescaleModel (Time-Series Data)

**Use for:** Data with timestamps that grows continuously over time

**Example: EventModel**
```python
from timescaledb import TimescaleModel

class EventModel(TimescaleModel, table=True):
    page: str
    user_agent: Optional[str]
    # ... other fields
    
    __chunk_time_interval__ = "INTERVAL 1 day"
    __drop_after__ = "INTERVAL 3 months"
```

**Why TimescaleModel for Events:**
- ✅ Automatic timestamp field (`time`)
- ✅ Data partitioned by time (hypertables)
- ✅ Optimized for time-range queries
- ✅ Automatic data retention policies
- ✅ Efficient aggregations with `time_bucket()`
- ✅ Handles millions/billions of rows

**Characteristics:**
- Continuous inserts (high write volume)
- Rarely updated or deleted
- Queries typically filter by time range
- Data grows indefinitely

### SQLModel (Standard Relational Data)

**Use for:** Traditional CRUD operations, reference data, user management

**Example: User Model**
```python
from sqlmodel import SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    username: str
    # ... other fields
```

**Why SQLModel for Users:**
- ✅ Standard CRUD operations (Create, Read, Update, Delete)
- ✅ Relationships with other tables
- ✅ Unique constraints and indexes
- ✅ Relatively small dataset
- ✅ Frequent updates and modifications

**Characteristics:**
- Low to moderate write volume
- Frequently updated
- Relational queries (joins, foreign keys)
- Bounded dataset size

## Our Architecture Decision

### Tables Using TimescaleModel
1. **EventModel** - Page view events
   - High volume: thousands/millions per day
   - Time-based queries: "events in last 24 hours"
   - No updates: events are immutable
   - Auto-retention: drop data after 3 months

### Tables Using SQLModel
1. **User** - User accounts
   - Low volume: hundreds to thousands
   - Random access: "get user by username"
   - Frequent updates: profile changes, password resets
   - No automatic time partitioning needed

## Benefits of This Approach

### Performance
- Time-series queries on events are blazingly fast
- User lookups remain simple and efficient
- No overhead of time-partitioning for user data

### Scalability
- Event table can grow to billions of rows
- User table stays manageable size
- Each optimized for its use case

### Maintenance
- Automatic event data cleanup (3 months)
- User data persists indefinitely
- Clear separation of concerns

## Adding New Models - Decision Guide

Ask these questions:

1. **Does this data have a timestamp and grow continuously?**
   - Yes → Consider TimescaleModel
   - No → Use SQLModel

2. **Will there be millions of rows?**
   - Yes → TimescaleModel (with partitioning)
   - No → SQLModel

3. **Are queries mostly time-based?**
   - Yes → TimescaleModel
   - No → SQLModel

4. **Is data write-mostly (rarely updated)?**
   - Yes → TimescaleModel
   - No → SQLModel

### Examples

**Use TimescaleModel:**
- ✅ Events, logs, metrics
- ✅ Sensor data, IoT readings
- ✅ Financial transactions (time-series view)
- ✅ Click streams, web analytics

**Use SQLModel:**
- ✅ Users, accounts, profiles
- ✅ Products, categories, tags
- ✅ Configuration, settings
- ✅ Relationships (friends, followers)

## Mixed Approach Example

You might have BOTH for the same concept:

```python
# Transaction record (immutable history)
class TransactionEvent(TimescaleModel, table=True):
    user_id: int
    amount: float
    status: str
    __chunk_time_interval__ = "INTERVAL 1 week"

# Account balance (current state)
class Account(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id")
    current_balance: float
    last_updated: datetime
```

## Resources

- [TimescaleDB Documentation](https://docs.timescale.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Time-Series vs Relational](https://docs.timescale.com/use-timescale/latest/schema-management/)
