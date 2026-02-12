from googleapiclient.discovery import build


def get_email_service(credentials):
    return build("gmail" , "v1" , credentials=credentials)



def fetch_latest_emails(service, max_results=10 ,after_ts = None):

    q = None

    if after_ts:
        q = f"after:{after_ts}" # unix timestamp in milliseconds

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        q=q
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



