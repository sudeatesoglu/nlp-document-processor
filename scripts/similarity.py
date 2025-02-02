import spacy
import numpy as np
import pymupdf
from spacy.matcher import Matcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from text_processing import *

nlp = spacy.load("en_core_web_md")


def check_cosine_similarity(doc_type, doc_1, doc_2):
    document_1, document_2 = process_document(doc_type, doc_1, doc_2)
    documents = [document_1, document_2]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    similarity_matrix = cosine_similarity(tfidf_matrix)

    return similarity_matrix[0, 1]


def check_doc_similarity(doc_type, doc_1, doc_2):
    document_1, document_2 = process_document(doc_type, doc_1, doc_2)

    doc_1_token = nlp(document_1)
    doc_2_token = nlp(document_2)

    similarity = round(doc_1_token.similarity(doc_2_token), 2)
    return "Similarity score of documents: ", similarity


def check_categorical_similarity(category, doc_type, doc):
    document = read_document(doc_type, doc)
    document = preprocess_text(document)
    category = preprocess_text(category)

    category_token = nlp(category)
    document_token = nlp(document)

    similarity = round(document_token.similarity(category_token), 2)
    return f"Similarity according to category: {similarity}"


def catch_related_words(word):
    word_vector = nlp.vocab.vectors[nlp.vocab.strings[word]]
    most_similar_words = nlp.vocab.vectors.most_similar(np.asarray([word_vector]), n=50)
    similar_words_list = [nlp.vocab.strings[w] for w in most_similar_words[0][0]]
    return similar_words_list


def highlight_pattern(pdf_path, pattern):
    output_path = pdf_path.replace(".pdf", "_highlighted.pdf")

    pdf_document = pymupdf.open(pdf_path)

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        process_page(page, pattern)

    pdf_document.save(output_path)
    pdf_document.close()

    return output_path


def process_page(page, pattern):
    search_result = page.search_for(pattern, quads=True)
    for quad in search_result:
        highlight = page.add_highlight_annot(quad)
        highlight.update()


def match_pattern(pattern, doc_type, doc):
    document = read_document(doc_type, doc)
    document = preprocess_text(document)
    document_token = nlp(document)

    pattern_list = [{"LOWER" : pattern}]

    matcher = Matcher(nlp.vocab)
    matcher.add("matcher", [pattern_list])
    matches = matcher(document_token)

    matched_info = []
    for match_id, start, end in matches:
        matched_span = document_token[start:end]
        matched_info.append({
            "Start token": start,
            "End token": end,
            "Matched part": matched_span.text
        })

    return matched_info


def pattern_interface(pattern, doc_type, doc):
    highlighted_file = highlight_pattern(doc, pattern)
    matched_info = match_pattern(pattern, doc_type, doc)
    return highlighted_file, matched_info


def highlight_similar_words(pdf_1, pdf_2):
    document_1, document_2 = process_document("PDF", pdf_1.name, pdf_2.name)
    doc_1_token = nlp(document_1)
    similar_words = set([token.text for token in doc_1_token if token.text in document_2])

    output_1 = pdf_1.name.replace(".pdf", "_highlighted.pdf")
    output_2 = pdf_2.name.replace(".pdf", "_highlighted.pdf")

    for pdf, output in zip([pdf_1.name, pdf_2.name], [output_1, output_2]):
        pdf_doc = pymupdf.open(pdf)
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            for word in similar_words:
                rects = page.search_for(word)
                for rect in rects:
                    page.add_highlight_annot(rect)
        pdf_doc.save(output)

    return output_1, output_2
