# Patheazy Labs Chatbot Static Menus and Flows

# Main Menu Options
MAIN_MENU = {
    "text": "Hello! Welcome to Patheazy Labs\nEasy Path To Quality Diagnostics",
    "buttons": [
        {"title": "Book a Lab Test", "payload": "FLOW_BOOK_LAB"},
        {"title": "Connect with the live Agent", "payload": "FLOW_CONNECT_AGENT"}
    ]
}

BOOK_LAB_MENU = {
    "text": "Great! Let's book your lab test.\nPlease choose your booking type:",
    "buttons": [
        {"title": "Home Collection — Doorstep Visit", "payload": "BOOK_HOME"},
        {"title": "Walk-in — Nearest Centre", "payload": "BOOK_WALKIN"}
    ]
}
