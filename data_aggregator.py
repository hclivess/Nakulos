import logging
from datetime import datetime, timedelta
from database import get_db

logger = logging.getLogger(__name__)

def aggregate_data():
    logger.info("Starting data aggregation...")
    db = get_db()

    try:
        with db.conn.cursor() as cursor:
            # Ensure the unique constraint exists
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'unique_metric_timestamp'
                    ) THEN
                        ALTER TABLE metrics 
                        ADD CONSTRAINT unique_metric_timestamp 
                        UNIQUE (host_id, metric_name, timestamp);
                    END IF;
                END $$;
            """)

            # Define aggregation periods
            aggregation_periods = [
                # Data older than 7 days but newer than 30 days:
                # Aggregate to hourly intervals
                (timedelta(days=7), 'hour'),

                # Data older than 30 days but newer than 90 days:
                # Aggregate to daily intervals
                (timedelta(days=30), 'day'),

                # Data older than 90 days but newer than 365 days:
                # Aggregate to weekly intervals
                (timedelta(days=90), 'week'),
            ]

            for retention_period, interval in aggregation_periods:
                aggregate_period(cursor, retention_period, interval)

            # Delete data older than 1 year
            delete_old_data(cursor, timedelta(days=365))

            db.conn.commit()
            logger.info("Data aggregation complete.")
    except Exception as e:
        db.conn.rollback()
        logger.error(f"An error occurred during data aggregation: {str(e)}")

def aggregate_period(cursor, retention_period, interval):
    end_date = datetime.now() - retention_period
    start_date = end_date - retention_period

    cursor.execute("""
        WITH aggregated_data AS (
            SELECT 
                host_id,
                metric_name,
                date_trunc(%s, to_timestamp(timestamp)) as bucket,
                AVG(value) as avg_value
            FROM metrics
            WHERE timestamp >= %s AND timestamp < %s
            GROUP BY host_id, metric_name, bucket
        ),
        deleted_data AS (
            DELETE FROM metrics
            WHERE timestamp >= %s AND timestamp < %s
            RETURNING host_id, metric_name, timestamp, value
        )
        INSERT INTO metrics (host_id, metric_name, timestamp, value)
        SELECT 
            host_id, 
            metric_name, 
            EXTRACT(EPOCH FROM bucket),
            avg_value
        FROM aggregated_data
        ON CONFLICT (host_id, metric_name, timestamp) 
        DO UPDATE SET value = EXCLUDED.value
    """, (interval, start_date.timestamp(), end_date.timestamp(),
          start_date.timestamp(), end_date.timestamp()))

    logger.info(f"Aggregated data to {interval} intervals for period ending {end_date}")

def delete_old_data(cursor, max_age):
    cutoff_date = datetime.now() - max_age
    cursor.execute("DELETE FROM metrics WHERE timestamp < %s", (cutoff_date.timestamp(),))
    logger.info(f"Deleted data older than {cutoff_date}")