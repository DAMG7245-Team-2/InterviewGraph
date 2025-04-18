import asyncio
from enum import Enum
import random

from sqlalchemy import Engine, text


def get_context():
    context = [
        """What is a Unix shell? Is Bash the only Unix shell?
A Unix shell is a software that provides a user interface for the underlying operating system. Unix shells typically provide a textual user interface - a command line interpreter - that may be used for entering and running commands, or create scripts that run a series of commands and can be used to express more advanced behavior.

Bash is not the only Unix shell, but just one of many. Short for Bourne-Again Shell, it is also one of the many Bourne-compatible shells. However, Bash is arguably one of the most popular shells around. There are other, modern shells available that often retain backwards compatibility with Bash but provide more functionality and features, such as the Z Shell (zsh).""",
        """What are shared, slave, private, and unbindable mountpoints?
A mount point that is shared may be replicated as many times as needed, and each copy will continue to be the exact same. Other mount points that appear under a shared mount point in some subdirectory will appear in all the other replicated mount points as it is.

A slave mount point is similar to a shared mount point with the small exception that the “sharing” of mount point information happens in one direction. A mount point that is slave will only receive mount and unmount events. Anything that is mounted under this replicated mount point will not move towards the original mount point.

A private mount point is exactly what the name implies: private. Mount points that appear under a private mount point will not be shown elsewhere in the other replicated mount points unless they are explicitly mounted there as well.

An unbindable mount point, which by definition is also private, cannot be replicated elsewhere through the use of the bind flag of the mount system call or command.""",
        """What is a swap space?
Swap space is a certain amount of space used by Linux to temporarily hold some programs that are running concurrently. This happens when RAM does not have enough memory to hold all programs that are executing.""",
    ]
    return context


class AvailableCategories(Enum):
    ALGORITHMS = "Algorithms"
    DATA_STRUCTURES = "Data structures"
    NETWORKS = "Networks"
    DEVOPS = "DevOps"
    JAVA = "Java"
    WEB_DEVELOPMENT = "Web Development"
    SOFTWARE_TESTING = "Software Testing"
    VERSION_CONTROL = "Version Control"
    SECURITY = "Security"
    FRONT_END = "Front-end"
    BACK_END = "Back-end"
    MACHINE_LEARNING = "Machine Learning"
    DISTRIBUTED_SYSTEMS = "Distributed Systems"
    DATA_ENGINEERING = "Data Engineering"
    FULL_STACK = "Full-stack"
    LOW_LEVEL_SYSTEMS = "Low-level Systems"
    DATABASE_AND_SQL = "Database and SQL"
    SYSTEM_DESIGN = "System Design"


class AvailableDifficulties(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


def get_interview_questions(
    engine: Engine,
    category: AvailableCategories,
    difficulty: AvailableDifficulties,
) -> list[str]:
    """Get interview questions from Snowflake database."""
    conn = engine.connect()
    result = conn.execute(
        text(
            f"SELECT Question, Answer FROM interview_questions WHERE category = '{category.value}' AND difficulty = '{difficulty.value}'"
        )
    )
    results = result.fetchall()
    conn.close()
    return results


def random_choices(
    results: list[tuple[str, str]], num_questions: int
) -> list[tuple[str, str]]:
    return random.choices(results, k=num_questions)


async def aget_randomized_interview_questions(
    engine: Engine,
    category: AvailableCategories,
    difficulty: AvailableDifficulties,
    num_questions: int,
) -> list[tuple[str, str]]:
    if num_questions <= 0:
        raise ValueError("Number of questions must be greater than 0")
    return random_choices(
        await asyncio.to_thread(get_interview_questions, engine, category, difficulty),
        num_questions,
    )
