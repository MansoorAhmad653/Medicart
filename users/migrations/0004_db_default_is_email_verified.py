# Add database-level DEFAULT for is_email_verified to prevent null errors

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_set_existing_users_verified'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE users_customuser ALTER COLUMN is_email_verified SET DEFAULT false;",
            reverse_sql="ALTER TABLE users_customuser ALTER COLUMN is_email_verified DROP DEFAULT;",
        ),
        # Also set any existing null values to false
        migrations.RunSQL(
            sql="UPDATE users_customuser SET is_email_verified = false WHERE is_email_verified IS NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
