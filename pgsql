ai-email-assistant/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── core/
│   │   │   ├── config.py        # env, settings
│   │   │   ├── security.py      # token encryption, secrets
│   │   │   └── logging.py
│   │   │
│   │   ├── auth/
│   │   │   ├── google_oauth.py  # OAuth flow logic
│   │   │   └── routes.py        # /login, /callback endpoints
│   │   │
│   │   ├── email/
│   │   │   ├── gmail_client.py  # Gmail API wrapper
│   │   │   ├── parser.py        # extract subject, sender, body
│   │   │   └── cleaner.py       # strip HTML, signatures, replies
│   │   │
│   │   ├── indexing/
│   │   │   ├── initial_sync.py  # fetch first 10 emails
│   │   │   ├── background.py    # older inbox indexing
│   │   │   └── incremental.py   # new email sync
│   │   │
│   │   ├── embeddings/
│   │   │   ├── embedder.py      # embedding logic (LangChain wrapper)
│   │   │   └── vectorstore.py   # FAISS / Chroma init
│   │   │
│   │   ├── rag/
│   │   │   ├── retriever.py     # semantic retrieval
│   │   │   ├── prompts.py       # grounded prompts
│   │   │   └── graph.py         # LangGraph flow
│   │   │
│   │   ├── db/
│   │   │   ├── models.py        # User, EmailMeta, IndexState
│   │   │   └── session.py       # DB connection
│   │   │
│   │   └── utils/
│   │       └── text.py          # token counting, helpers
│   │
│   ├── tests/
│   │   └── test_email_cleaner.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   └── (later: Streamlit or React)
│
├── docker-compose.yml           # optional later
├── README.md
└── .gitignore
