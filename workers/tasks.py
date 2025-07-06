from config import env
from celery import Celery

broker_transport_options = {
    'region': env.AWS_REGION,
    'visibility_timeout': 3600,  # 1 hour
    'polling_interval': 5,  # seconds
    'predefined_queues': {
        'default': {
            'url': env.SQS_DEFAULT_QUEUE_URL,
        }
    },
}
app = Celery("tasks")

app.conf.broker_url = env.SQS_BROKER_URL
app.conf.broker_transport_options = broker_transport_options
app.conf.task_default_queue = 'default'