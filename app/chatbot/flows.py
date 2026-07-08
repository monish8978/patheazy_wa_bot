# Patheazy Labs Chatbot Static Menus and Flows

# Main Menu Options
MAIN_MENU = {
    "text": "Hello! Welcome to Patheazy Labs\nEasy Path To Quality Diagnostics",
    "buttons": [
        {"title": "Book a Lab Test", "payload": "FLOW_BOOK_LAB"},
        {"title": "Connect to Live Agent", "payload": "connect to live"}
    ]
}

BOOK_LAB_MENU = {
    "text": "Great! Let's book your lab test.\nPlease choose your booking type:",
    "buttons": [
        {"title": "Home Collection", "payload": "BOOK_HOME"},
        {"title": "Walk-in Centre", "payload": "BOOK_WALKIN"}
    ]
}
