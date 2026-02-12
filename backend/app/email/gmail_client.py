from googleapiclient.discovery import build


def get_email_service(credentials):
    return build("gmail" , "v1" , credentials=credentials)



def fetch_latest_emails(service, max_results=10):
    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
    ).execute()
    messages = results.get("messages" ,[])
    return messages



def fetch_email_detail(service, msg_id):
    message = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full"
    ).execute()
    return message



