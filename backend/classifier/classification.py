# from transformers import pipeline

# classifier = pipeline("text-classification",
#                       model="distilbert-base-uncased")

# print(classifier("Please approve my leave request"))

from transformers import pipeline

classifier = pipeline("zero-shot-classification",
                      model="facebook/bart-large-mnli")

classifier(
    "Please update my salary slip",
    candidate_labels=["HR","Finance","IT","Support"]
)