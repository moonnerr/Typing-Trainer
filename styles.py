DARK_THEME = {
    "background": "#171821",
    "sidebar": "#1D1E29",
    "panel": "#22232F",
    "panel_border": "#30313F",

    "text": "#E8E8F0",
    "secondary_text": "#9293A5",
    "stat_title": "#9293A5",

    "accent": "#A77BFF",
    "accent_hover": "#B995FF",
    "accent_pressed": "#8959E8",

    "button": "#292A38",
    "button_hover": "#353648",
    "button_pressed": "#414257",

    "card": "#22232F",
    "card_border": "#30313F",

    "input": "#292A38",
    "selection": "#A77BFF",
}


LIGHT_THEME = {
    "background": "#F5F6FA",
    "sidebar": "#FFFFFF",
    "panel": "#FFFFFF",
    "panel_border": "#E8EAF0",

    "text": "#25263A",
    "secondary_text": "#85889B",
    "stat_title": "#85889B",

    "accent": "#8B5CF6",
    "accent_hover": "#7C3AED",
    "accent_pressed": "#6D28D9",

    "button": "#F3F1FA",
    "button_hover": "#EEE9FB",
    "button_pressed": "#E6DDF8",

    "card": "#FFFFFF",
    "card_border": "#E8EAF0",

    "input": "#FFFFFF",
    "selection": "#DCCBFF",
}


def get_stylesheet(theme):

    return f"""
    QMainWindow {{
        background-color: {theme["background"]};
    }}

    QWidget {{
        color: {theme["text"]};
        font-family: "Segoe UI";
        font-size: 14px;
    }}

    QWidget#mainContainer {{
        background-color: {theme["background"]};
    }}

    QWidget#sidebar {{
        background-color: {theme["sidebar"]};
        border-right: 1px solid {theme["panel_border"]};
    }}

    QWidget#trainingPanel {{
        background-color: {theme["panel"]};
        border: 1px solid {theme["panel_border"]};
        border-radius: 14px;
    }}

    QWidget#statsPanel {{
        background-color: {theme["background"]};
    }}

    QLabel {{
        color: {theme["text"]};
        background: transparent;
    }}

    QTextBrowser {{
        background-color: {theme["panel"]};
        color: {theme["text"]};
        border: none;
        padding: 14px;
        font-size: 18px;
        selection-background-color: {theme["selection"]};
        border-radius: 10px;
    }}

    QPushButton {{
        background-color: {theme["button"]};
        color: {theme["text"]};
        border: 1px solid {theme["panel_border"]};
        border-radius: 12px;
        padding: 12px 14px;
        text-align: center;
        font-size: 14px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {theme["button_hover"]};
        border: 1px solid {theme["accent"]};
    }}

    QPushButton:pressed {{
        background-color: {theme["button_pressed"]};
        border: 1px solid {theme["accent_pressed"]};
    }}

    QPushButton:disabled {{
        color: {theme["secondary_text"]};
        background-color: {theme["panel"]};
        border: 1px solid {theme["panel_border"]};
    }}

    QSlider::groove:horizontal {{
        height: 6px;
        background: {theme["panel_border"]};
        border-radius: 3px;
    }}

    QSlider::sub-page:horizontal {{
        background: {theme["accent"]};
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: {theme["accent"]};
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {theme["accent_hover"]};
    }}

    QWidget#statCard {{
        background-color: {theme["card"]};
        border: 1px solid {theme["card_border"]};
        border-radius: 12px;
    }}

    QLabel#statTitle {{
        color: {theme["stat_title"]};
        font-size: 11px;
        font-weight: bold;
    }}

    QLabel#statValue {{
        color: {theme["accent"]};
        font-size: 25px;
        font-weight: bold;
    }}
    
    QLabel#sectionTitle {{
        color: {theme["secondary_text"]};
        font-size: 12px;
        font-weight: bold;
        padding-top: 18px;
        padding-bottom: 6px;
        letter-spacing: 1px;
    }}
    """
