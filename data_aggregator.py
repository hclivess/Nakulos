import logging
from datetime import datetime, timedelta
from database import get_db

logger = logging.getLogger(__name__)


def aggregate_data():
    logger.info("Starting data aggregation...")
    db = get_db()

    try:
        with db.conn.cursor() as cursor:
            # Define aggregation intervals
            intervals = [
                ('hour', timedelta(days=7)),  # Hourly data for the last week
                ('day', timedelta(days=30)),  # Daily data for the last month
                ('week', timedelta(days=365)),  # Weekly data for the last year
            ]

            for interval, retention_period in intervals:
                cutoff_date = datetime.now() - retention_period

                # Create temporary table for aggregated data
                cursor.execute(f"""
                    CREATE TEMPORARY TABLE temp_aggregated_metrics AS
                    SELECT 
                        host_id,
                        metric_name,
                        date_trunc(%s, to_timestamp(timestamp)) as agg_timestamp,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value
                    FROM metrics
                    WHERE timestamp < %s
                    GROUP BY host_id, metric_name, date_trunc(%s, to_timestamp(timestamp))
                """, (interval, cutoff_date.timestamp(), interval))

                # Insert aggregated data into metrics table
                cursor.execute("""
                    INSERT INTO metrics (host_id, metric_name, timestamp, value)
                    SELECT host_id, metric_name, EXTRACT(EPOCH FROM agg_timestamp), avg_value
                    FROM temp_aggregated_metrics
                """)

                # Delete original granular data
                cursor.execute("""
                    DELETE FROM metrics
                    WHERE timestamp < %s AND timestamp >= %s
                    AND (host_id, metric_name, timestamp) NOT IN (
                        SELECT host_id, metric_name, EXTRACT(EPOCH FROM agg_timestamp)
                        FROM temp_aggregated_metrics
                    )
                """, (cutoff_date.timestamp(), (cutoff_date - retention_period).timestamp()))

                # Drop temporary table
                cursor.execute("DROP TABLE temp_aggregated_metrics")

            db.conn.commit()
            logger.info("Data aggregation complete.")
    except Exception as e:
        db.conn.rollback()
        logger.error(f"An error occurred during data aggregation: {str(e)}")