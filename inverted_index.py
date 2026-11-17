import re
from collections import Counter
from pymongo import MongoClient


client = MongoClient("mongodb://localhost:27017/")
db = client["assignment3"]

documents = db["documents"]
inverted_index = db["inverted_index"]


def tokenize(text):
    """Lowercase text, remove punctuation, and split into terms."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text.split()


def remove_document_from_index(doc_id):
    """Remove all postings for a document and empty terms."""
    for index_document in list(inverted_index.find({})):
        updated_postings = [
            posting
            for posting in index_document["postings"]
            if posting["docId"] != doc_id
        ]

        if updated_postings:
            inverted_index.update_one(
                {"_id": index_document["_id"]},
                {"$set": {"postings": updated_postings}}
            )
        else:
            inverted_index.delete_one({"_id": index_document["_id"]})


def add_document_to_index(doc_id, text):
    """Add a document's terms and term frequencies to the index."""
    term_frequencies = Counter(tokenize(text))

    for term, frequency in term_frequencies.items():
        index_document = inverted_index.find_one({"term": term})
        new_posting = {"docId": doc_id, "tf": frequency}

        if index_document is None:
            inverted_index.insert_one({
                "term": term,
                "postings": [new_posting]
            })
        else:
            postings = [
                posting
                for posting in index_document["postings"]
                if posting["docId"] != doc_id
            ]
            postings.append(new_posting)
            postings.sort(key=lambda posting: posting["docId"])

            inverted_index.update_one(
                {"_id": index_document["_id"]},
                {"$set": {"postings": postings}}
            )


def obtain_or_update_document(doc_id, text):
    """Insert a new document or update an existing document."""
    if documents.find_one({"_id": doc_id}) is not None:
        remove_document_from_index(doc_id)

    documents.replace_one(
        {"_id": doc_id},
        {"_id": doc_id, "text": text},
        upsert=True
    )
    add_document_to_index(doc_id, text)


def delete_document(doc_id):
    """Delete a document and its postings from the index."""
    remove_document_from_index(doc_id)
    documents.delete_one({"_id": doc_id})


def print_collections():
    print("Documents collection:")
    for document in documents.find().sort("_id", 1):
        print(document)

    print("\nInverted index collection:")
    for index_document in inverted_index.find().sort("term", 1):
        print(index_document)


# Clear collections so the program can be rerun consistently.
documents.delete_many({})
inverted_index.delete_many({})

# Operation 1
obtain_or_update_document(
    1,
    "Summer rain is common in Florida."
)

# Operation 2
obtain_or_update_document(
    2,
    "Summer is hot in Arizona."
)

# Operation 3
obtain_or_update_document(
    1,
    "Summer rain is hot rain in Florida."
)

# Operation 4
obtain_or_update_document(
    3,
    "Hot summer rain in California."
)

# Operation 5
delete_document(2)

# Operation 6
print_collections()
