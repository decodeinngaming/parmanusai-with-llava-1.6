"""
Working implementation of self-learning and self-improving capabilities for ParManusAI.
This module provides practical learning mechanisms that can be integrated immediately.
"""

import asyncio
import hashlib
import json
import re
import sqlite3
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LearningRecord:
    """Record of an agent's learning experience."""

    task_id: str
    user_request: str
    agent_used: str
    success: bool
    execution_time: float
    error_message: Optional[str]
    user_feedback_score: Optional[int]  # 1-5 rating
    timestamp: datetime
    context: Dict[str, Any]  # Additional context like file types, complexity


@dataclass
class ImprovementPattern:
    """A learned improvement pattern."""

    pattern_id: str
    trigger_conditions: Dict[str, Any]
    suggested_actions: List[str]
    confidence_score: float
    success_count: int
    total_usage: int
    last_updated: datetime


class SelfLearningEngine:
    """Self-learning engine that tracks performance and suggests improvements."""

    def __init__(self, db_path: str = "parmanusai_learning.db"):
        self.db_path = Path(db_path)
        self.learning_records = []
        self.improvement_patterns = {}
        self.performance_metrics = {}
        self._init_database()
        self._load_existing_patterns()

    def _init_database(self):
        """Initialize the learning database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Learning records table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE,
                user_request TEXT,
                agent_used TEXT,
                success BOOLEAN,
                execution_time REAL,
                error_message TEXT,
                user_feedback_score INTEGER,
                timestamp TEXT,
                context TEXT
            )
        """
        )

        # Improvement patterns table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS improvement_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE,
                trigger_conditions TEXT,
                suggested_actions TEXT,
                confidence_score REAL,
                success_count INTEGER,
                total_usage INTEGER,
                last_updated TEXT
            )
        """
        )

        # Performance metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def record_task_execution(self, record: LearningRecord):
        """Record a task execution for learning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO learning_records
                (task_id, user_request, agent_used, success, execution_time,
                 error_message, user_feedback_score, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.task_id,
                    record.user_request,
                    record.agent_used,
                    record.success,
                    record.execution_time,
                    record.error_message,
                    record.user_feedback_score,
                    record.timestamp.isoformat(),
                    json.dumps(record.context),
                ),
            )

            conn.commit()
            self.learning_records.append(record)

            # Trigger pattern analysis
            asyncio.create_task(self._analyze_patterns())

        except Exception as e:
            print(f"Error recording task execution: {e}")
        finally:
            conn.close()

    async def _analyze_patterns(self):
        """Analyze recent records to identify improvement patterns."""
        try:
            recent_records = self._get_recent_records(days=7)

            # Analyze success/failure patterns
            self._analyze_success_patterns(recent_records)
            self._analyze_failure_patterns(recent_records)
            self._analyze_performance_patterns(recent_records)

            # Update metrics
            self._update_performance_metrics()

        except Exception as e:
            print(f"Error analyzing patterns: {e}")

    def _analyze_success_patterns(self, records: List[LearningRecord]):
        """Analyze successful executions to learn what works."""
        successful_records = [r for r in records if r.success]

        # Group by request type
        request_patterns = defaultdict(list)
        for record in successful_records:
            pattern_key = self._extract_request_pattern(record.user_request)
            request_patterns[pattern_key].append(record)

        # Create improvement patterns for successful approaches
        for pattern_key, pattern_records in request_patterns.items():
            if len(pattern_records) >= 2:  # Need at least 2 successes
                avg_time = sum(r.execution_time for r in pattern_records) / len(
                    pattern_records
                )

                pattern = ImprovementPattern(
                    pattern_id=f"success_{hashlib.md5(pattern_key.encode()).hexdigest()[:8]}",
                    trigger_conditions={
                        "request_pattern": pattern_key,
                        "context_similarity": 0.8,
                    },
                    suggested_actions=[
                        f"Use {pattern_records[0].agent_used} agent",
                        f"Expected execution time: {avg_time:.2f}s",
                    ],
                    confidence_score=min(0.9, len(pattern_records) * 0.2),
                    success_count=len(pattern_records),
                    total_usage=len(pattern_records),
                    last_updated=datetime.now(),
                )

                self._store_improvement_pattern(pattern)

    def _analyze_failure_patterns(self, records: List[LearningRecord]):
        """Analyze failed executions to learn what to avoid."""
        failed_records = [r for r in records if not r.success]

        # Group by error type
        error_patterns = defaultdict(list)
        for record in failed_records:
            if record.error_message:
                error_type = self._classify_error(record.error_message)
                error_patterns[error_type].append(record)

        # Create avoidance patterns
        for error_type, error_records in error_patterns.items():
            if len(error_records) >= 2:  # Need at least 2 failures
                pattern = ImprovementPattern(
                    pattern_id=f"avoid_{hashlib.md5(error_type.encode()).hexdigest()[:8]}",
                    trigger_conditions={"error_risk": error_type, "context_match": 0.7},
                    suggested_actions=[
                        f"Avoid using {error_records[0].agent_used} for similar requests",
                        f"Add error handling for {error_type}",
                        "Consider alternative approach",
                    ],
                    confidence_score=min(0.8, len(error_records) * 0.3),
                    success_count=0,
                    total_usage=len(error_records),
                    last_updated=datetime.now(),
                )

                self._store_improvement_pattern(pattern)

    def _analyze_performance_patterns(self, records: List[LearningRecord]):
        """Analyze performance to identify optimization opportunities."""
        # Find slow executions
        avg_time = (
            sum(r.execution_time for r in records) / len(records) if records else 0
        )
        slow_records = [r for r in records if r.execution_time > avg_time * 2]

        if slow_records:
            pattern = ImprovementPattern(
                pattern_id="performance_optimization",
                trigger_conditions={"execution_time_threshold": avg_time * 1.5},
                suggested_actions=[
                    "Consider caching for repeated operations",
                    "Optimize file I/O operations",
                    "Add progress indicators for long operations",
                ],
                confidence_score=0.6,
                success_count=0,
                total_usage=len(slow_records),
                last_updated=datetime.now(),
            )

            self._store_improvement_pattern(pattern)

    def get_improvement_suggestions(
        self, user_request: str, context: Dict[str, Any]
    ) -> List[str]:
        """Get improvement suggestions for a current request."""
        suggestions = []

        request_pattern = self._extract_request_pattern(user_request)

        for pattern in self.improvement_patterns.values():
            if self._pattern_matches(pattern, request_pattern, context):
                suggestions.extend(pattern.suggested_actions)

        return suggestions

    def get_performance_insights(self) -> Dict[str, Any]:
        """Get current performance insights and trends."""
        recent_records = self._get_recent_records(days=30)

        if not recent_records:
            return {"message": "No recent data available"}

        success_rate = sum(1 for r in recent_records if r.success) / len(recent_records)
        avg_execution_time = sum(r.execution_time for r in recent_records) / len(
            recent_records
        )

        agent_performance = defaultdict(list)
        for record in recent_records:
            agent_performance[record.agent_used].append(record)

        agent_stats = {}
        for agent, records in agent_performance.items():
            agent_success_rate = sum(1 for r in records if r.success) / len(records)
            agent_avg_time = sum(r.execution_time for r in records) / len(records)
            agent_stats[agent] = {
                "success_rate": agent_success_rate,
                "avg_execution_time": agent_avg_time,
                "total_tasks": len(records),
            }

        return {
            "overall_success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "total_tasks": len(recent_records),
            "agent_performance": agent_stats,
            "improvement_patterns": len(self.improvement_patterns),
            "last_updated": datetime.now().isoformat(),
        }

    def suggest_code_improvements(
        self, file_path: str, performance_issue: str
    ) -> List[str]:
        """Suggest specific code improvements based on learned patterns."""
        suggestions = []

        # Analyze performance issue
        if "timeout" in performance_issue.lower():
            suggestions.extend(
                [
                    "Add timeout handling with configurable limits",
                    "Implement exponential backoff for retries",
                    "Add progress indicators for long operations",
                    "Consider breaking large operations into smaller chunks",
                ]
            )

        if "memory" in performance_issue.lower():
            suggestions.extend(
                [
                    "Implement lazy loading for large objects",
                    "Add memory cleanup after operations",
                    "Use generators instead of lists for large datasets",
                    "Consider streaming for file operations",
                ]
            )

        if "error" in performance_issue.lower():
            suggestions.extend(
                [
                    "Add specific exception handling",
                    "Implement graceful fallback mechanisms",
                    "Add detailed error logging",
                    "Create user-friendly error messages",
                ]
            )

        # Add suggestions based on learned patterns
        for pattern in self.improvement_patterns.values():
            if pattern.confidence_score > 0.7:
                suggestions.extend(pattern.suggested_actions)

        return list(set(suggestions))  # Remove duplicates

    def _extract_request_pattern(self, user_request: str) -> str:
        """Extract a pattern from user request for matching."""
        request_lower = user_request.lower()

        # Identify key patterns
        if any(word in request_lower for word in ["create", "generate", "make"]):
            if "html" in request_lower or "webpage" in request_lower:
                return "create_webpage"
            elif "css" in request_lower:
                return "create_css"
            elif "file" in request_lower:
                return "create_file"

        if any(word in request_lower for word in ["search", "find", "look"]):
            return "search_task"

        if any(word in request_lower for word in ["analyze", "check", "review"]):
            return "analysis_task"

        return "general_task"

    def _classify_error(self, error_message: str) -> str:
        """Classify error message into categories."""
        error_lower = error_message.lower()

        if "timeout" in error_lower:
            return "timeout_error"
        elif "permission" in error_lower or "access" in error_lower:
            return "permission_error"
        elif "not found" in error_lower or "404" in error_lower:
            return "not_found_error"
        elif "connection" in error_lower or "network" in error_lower:
            return "network_error"
        elif "memory" in error_lower:
            return "memory_error"
        else:
            return "general_error"

    def _pattern_matches(
        self, pattern: ImprovementPattern, request_pattern: str, context: Dict[str, Any]
    ) -> bool:
        """Check if a pattern matches the current context."""
        trigger_conditions = pattern.trigger_conditions

        if "request_pattern" in trigger_conditions:
            if trigger_conditions["request_pattern"] != request_pattern:
                return False

        if "context_similarity" in trigger_conditions:
            # Simple context matching (could be enhanced)
            required_similarity = trigger_conditions["context_similarity"]
            if pattern.confidence_score < required_similarity:
                return False

        return True

    def _store_improvement_pattern(self, pattern: ImprovementPattern):
        """Store an improvement pattern in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO improvement_patterns
                (pattern_id, trigger_conditions, suggested_actions, confidence_score,
                 success_count, total_usage, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern.pattern_id,
                    json.dumps(pattern.trigger_conditions),
                    json.dumps(pattern.suggested_actions),
                    pattern.confidence_score,
                    pattern.success_count,
                    pattern.total_usage,
                    pattern.last_updated.isoformat(),
                ),
            )

            conn.commit()
            self.improvement_patterns[pattern.pattern_id] = pattern

        except Exception as e:
            print(f"Error storing improvement pattern: {e}")
        finally:
            conn.close()

    def _load_existing_patterns(self):
        """Load existing patterns from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM improvement_patterns")
            rows = cursor.fetchall()

            for row in rows:
                pattern = ImprovementPattern(
                    pattern_id=row[1],
                    trigger_conditions=json.loads(row[2]),
                    suggested_actions=json.loads(row[3]),
                    confidence_score=row[4],
                    success_count=row[5],
                    total_usage=row[6],
                    last_updated=datetime.fromisoformat(row[7]),
                )
                self.improvement_patterns[pattern.pattern_id] = pattern

        except Exception as e:
            print(f"Error loading patterns: {e}")
        finally:
            conn.close()

    def _get_recent_records(self, days: int = 7) -> List[LearningRecord]:
        """Get recent learning records."""
        cutoff_date = datetime.now() - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT * FROM learning_records
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """,
                (cutoff_date.isoformat(),),
            )

            rows = cursor.fetchall()
            records = []

            for row in rows:
                record = LearningRecord(
                    task_id=row[1],
                    user_request=row[2],
                    agent_used=row[3],
                    success=row[4],
                    execution_time=row[5],
                    error_message=row[6],
                    user_feedback_score=row[7],
                    timestamp=datetime.fromisoformat(row[8]),
                    context=json.loads(row[9]) if row[9] else {},
                )
                records.append(record)

            return records

        except Exception as e:
            print(f"Error getting recent records: {e}")
            return []
        finally:
            conn.close()

    def _update_performance_metrics(self):
        """Update overall performance metrics."""
        recent_records = self._get_recent_records(days=30)

        if not recent_records:
            return

        metrics = {
            "success_rate": sum(1 for r in recent_records if r.success)
            / len(recent_records),
            "avg_execution_time": sum(r.execution_time for r in recent_records)
            / len(recent_records),
            "total_tasks": len(recent_records),
            "pattern_count": len(self.improvement_patterns),
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for metric_name, metric_value in metrics.items():
                cursor.execute(
                    """
                    INSERT INTO performance_metrics (metric_name, metric_value, timestamp)
                    VALUES (?, ?, ?)
                """,
                    (metric_name, metric_value, datetime.now().isoformat()),
                )

            conn.commit()

        except Exception as e:
            print(f"Error updating metrics: {e}")
        finally:
            conn.close()


# Integration wrapper for existing ParManusAI agents
class LearningEnabledAgent:
    """Wrapper that adds learning capabilities to existing agents."""

    def __init__(self, original_agent, learning_engine: SelfLearningEngine):
        self.original_agent = original_agent
        self.learning_engine = learning_engine
        self.current_task_id = None
        self.task_start_time = None

    async def step(self):
        """Enhanced step method with learning."""
        self.current_task_id = f"task_{int(time.time())}"
        self.task_start_time = time.time()

        # Get user request
        user_request = ""
        if hasattr(self.original_agent, "messages") and self.original_agent.messages:
            for msg in reversed(self.original_agent.messages):
                if msg.role == "user":
                    user_request = msg.content
                    break

        # Get improvement suggestions
        suggestions = self.learning_engine.get_improvement_suggestions(
            user_request, {"agent_type": self.original_agent.name}
        )

        if suggestions:
            print(f"💡 Learning suggestions: {suggestions[:2]}")  # Show top 2

        try:
            # Execute original agent logic
            result = await self.original_agent.step()

            # Record successful execution
            record = LearningRecord(
                task_id=self.current_task_id,
                user_request=user_request,
                agent_used=self.original_agent.name,
                success=True,
                execution_time=time.time() - self.task_start_time,
                error_message=None,
                user_feedback_score=None,
                timestamp=datetime.now(),
                context={
                    "agent_type": self.original_agent.name,
                    "result_length": len(str(result)) if result else 0,
                },
            )

            self.learning_engine.record_task_execution(record)

            return result

        except Exception as e:
            # Record failed execution
            record = LearningRecord(
                task_id=self.current_task_id,
                user_request=user_request,
                agent_used=self.original_agent.name,
                success=False,
                execution_time=time.time() - self.task_start_time,
                error_message=str(e),
                user_feedback_score=None,
                timestamp=datetime.now(),
                context={
                    "agent_type": self.original_agent.name,
                    "error_type": type(e).__name__,
                },
            )

            self.learning_engine.record_task_execution(record)

            # Re-raise the exception
            raise

    def __getattr__(self, name):
        """Delegate attribute access to the original agent."""
        return getattr(self.original_agent, name)


# Usage example and testing
if __name__ == "__main__":
    # Example usage
    learning_engine = SelfLearningEngine()

    # Simulate some task executions
    test_records = [
        LearningRecord(
            task_id="test_1",
            user_request="Create a webpage about AI",
            agent_used="file",
            success=True,
            execution_time=2.5,
            error_message=None,
            user_feedback_score=5,
            timestamp=datetime.now(),
            context={"file_type": "html"},
        ),
        LearningRecord(
            task_id="test_2",
            user_request="Create CSS for buttons",
            agent_used="file",
            success=True,
            execution_time=1.8,
            error_message=None,
            user_feedback_score=4,
            timestamp=datetime.now(),
            context={"file_type": "css"},
        ),
    ]

    for record in test_records:
        learning_engine.record_task_execution(record)

    # Get insights
    insights = learning_engine.get_performance_insights()
    print("Performance Insights:", json.dumps(insights, indent=2))
