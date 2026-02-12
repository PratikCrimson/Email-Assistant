import time
from app.email.gmail_client import get_email_service, fetch_latest_emails, fetch_email_detail
from app.email.parser import extract_email_feilds

def run_background_indexing(credentials , max_results=10):
    service = get_email_service(credentials)
    messages = fetch_latest_emails(service, max_results = max_results)
    total = len(messages)

    print(f"🔄 Starting background indexing: {total} emails found") 

    for i, msg in enumerate(messages, start=1):
        try:
            detail = fetch_email_detail(service, msg["id"])
            parsed = extract_email_feilds(detail)

            #TODO: store the parsed email in the database later 
            print(f"✅ Processed email {i}/{total}: | Subject: {parsed.get('subject')}")

            time.sleep(0.1)

        except Exception as e:
            print(f"❌ Error processing email {i}/{total}: {e}")
        
    print(f"🔄 Background indexing completed: {total} emails processed")