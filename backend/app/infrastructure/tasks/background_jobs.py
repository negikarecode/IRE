from app.core.celery_app import celery_app
import time

@celery_app.task(name="tasks.send_async_notification")
def send_async_notification(tenant_id: str, user_id: str, title: str, message: str):
    # Background worker task to dispatch emails/push notifications asynchronously
    time.sleep(1)
    return {"status": "SUCCESS", "tenant_id": tenant_id, "user_id": user_id}

@celery_app.task(name="tasks.process_document_async")
def process_document_async(tenant_id: str, document_id: str, file_path: str):
    # Background worker task for document OCR or extraction preprocessing
    time.sleep(2)
    return {"status": "PROCESSED", "document_id": document_id}
