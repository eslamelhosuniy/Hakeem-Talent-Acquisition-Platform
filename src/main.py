from src.helpers.name_classifier import extract_entities

if __name__ == "__main__":
    text = "Ahmed works at Google with Mohamed and Sara in Cairo on 12 March 2023"
    
    entities = extract_entities(text)

    # Categorize entities
    persons = [e['text'] for e in entities if e['label'] == "PERSON"]
    orgs = [e['text'] for e in entities if e['label'] == "ORG"]
    locations = [e['text'] for e in entities if e['label'] == "GPE"]
    dates = [e['text'] for e in entities if e['label'] == "DATE"]

    # Print summary in terminal
    if persons:
        print(f"Detected Persons: {', '.join(persons)}")
    if orgs:
        print(f"Detected Organizations: {', '.join(orgs)}")
    if locations:
        print(f"Detected Locations: {', '.join(locations)}")
    if dates:
        print(f"Detected Dates: {', '.join(dates)}")
