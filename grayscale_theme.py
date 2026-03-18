import re
import codecs

def process_css(css):
    # #6366f1 (indigo-500) -> #475569 (slate-600)
    # #8b5cf6 (violet-500) -> #64748b (slate-500)
    # rgba(99, 102, 241, x) -> rgba(71, 85, 105, x)
    # rgba(139, 92, 246, x) -> rgba(100, 116, 139, x)
    # rgba(236, 72, 153, x) -> rgba(148, 163, 184, x)
    
    rep = {
        '#6366f1': '#475569',
        '#8b5cf6': '#64748b',
        'rgba(99, 102, 241': 'rgba(71, 85, 105',
        'rgba(139, 92, 246': 'rgba(100, 116, 139',
        'rgba(236, 72, 153': 'rgba(148, 163, 184',
        'border: 1px solid rgba(99, 102, 241, 0.25)': 'border: 1px solid rgba(0, 0, 0, 0.15)',
    }
    for k, v in rep.items():
        css = css.replace(k, v)
    return css

def process_jsx(jsx):
    # Replace tailwind classes for indigo and violet with slate and gray
    # Examples:
    # bg-gradient-to-r from-indigo-500 to-violet-500 -> from-slate-600 to-gray-500
    # text-indigo-400 -> text-slate-500
    
    # We will use simple regex for indigo and violet
    jsx = re.sub(r'indigo-([1-9]00)', r'slate-\1', jsx)
    jsx = re.sub(r'violet-([1-9]00)', r'gray-\1', jsx)
    
    # Some specific replacements for the white/grey aesthetic
    jsx = jsx.replace("bg-indigo-50/50", "bg-slate-100")
    
    # Let's ensure navigation buttons and statuses (emerald/green) are kept, but if the user wants strictly white and grey everywhere:
    # "Theme in white and grey" usually means the main branding. We already made it light, now we change it to grayscale.
    
    return jsx

if __name__ == "__main__":
    with codecs.open('client/src/App.css', 'r', encoding='utf-8') as f:
        css = f.read()
    with codecs.open('client/src/App.jsx', 'r', encoding='utf-8') as f:
        jsx = f.read()

    css_out = process_css(css)
    jsx_out = process_jsx(jsx)

    with codecs.open('client/src/App.css', 'w', encoding='utf-8') as f:
        f.write(css_out)
    with codecs.open('client/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(jsx_out)
    print("Grayscale (white and grey) theme applied successfully.")
