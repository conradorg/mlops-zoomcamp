from prefect import flow, task
import random

# a @task decorator on each function called within the flow.
# a @flow decorator on the script’s entrypoint.


@task
def get_customer_ids() -> list[str]:
    # Fetch customer IDs from a database or API
    return [f"customer{n}" for n in random.choices(range(100), k=10)]

@task
def process_customer(customer_id: str) -> str:
    # Process a single customer
    return f"Processed {customer_id}"

@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    # Map the process_customer task across all customer IDs
    results = process_customer.map(customer_ids)
    return results


if __name__ == "__main__":
    main.serve(
        name="my-first-deployment",
        cron="*/2 * * * *" # run every 2 minutes
        #cron="0 8 * * *"  # Run every day at 8:00 AM
    )

