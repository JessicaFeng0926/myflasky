"""empty message

Revision ID: 54a2bb9917ab
Revises: c9dfce477653
Create Date: 2019-08-14 08:45:34.702253

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54a2bb9917ab'
down_revision = 'c9dfce477653'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'body_html')
    # ### end Alembic commands ###
