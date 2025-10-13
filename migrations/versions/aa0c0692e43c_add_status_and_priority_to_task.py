from alembic import op
import sqlalchemy as sa
from app.models.enums import TaskStatus, TaskPriority

# revision identifiers, used by Alembic.
revision = "aa0c0692e43c"
down_revision = "deb1e855b74d"
branch_labels = None
depends_on = None

# Enum
taskstatus = sa.Enum(TaskStatus, name="taskstatus")
taskpriority = sa.Enum(TaskPriority, name="taskpriority")
taskstatus.create(op.get_bind(), checkfirst=True)
taskpriority.create(op.get_bind(), checkfirst=True)


def upgrade() -> None:
    op.add_column(
        "tasks", sa.Column("status", taskstatus, nullable=False, server_default="TODO")
    )
    op.add_column(
        "tasks",
        sa.Column("priority", taskpriority, nullable=False, server_default="NONE"),
    )


def downgrade() -> None:
    op.drop_column("tasks", "status")
    op.drop_column("tasks", "priority")
    taskstatus.drop(op.get_bind(), checkfirst=True)
    taskpriority.drop(op.get_bind(), checkfirst=True)
