import re
import codecs

def process_css(css):
    rep = {
        '#475569': '#2563eb', # blue-600
        '#64748b': '#3b82f6', # blue-500
        'rgba(71, 85, 105': 'rgba(37, 99, 235',
        'rgba(100, 116, 139': 'rgba(59, 130, 246',
        'rgba(148, 163, 184': 'rgba(96, 165, 250',
    }
    for k, v in rep.items():
        css = css.replace(k, v)
    return css

def process_jsx(jsx):
    # Route line
    jsx = jsx.replace("'#6366f1'", "'#2563eb'")
    
    # Specific branding components that were grayscaled
    rep = {
        'from-slate-500 to-gray-600': 'from-blue-600 to-blue-500',
        'shadow-slate-500/20': 'shadow-blue-500/20',
        'from-slate-600 to-gray-600 hover:from-slate-500 hover:to-gray-500': 'from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400',
        'bg-slate-600 hover:bg-slate-500': 'bg-blue-600 hover:bg-blue-500',
        'from-slate-500 to-gray-500': 'from-blue-600 to-blue-500',
        'bg-slate-600/30 border border-slate-500/40': 'bg-blue-600/10 border border-blue-500/40',
        'text-slate-300 font-semibold\">STOP': 'text-blue-600 font-semibold\">STOP',
        'bg-slate-100 hover:bg-rose-600 text-white': 'bg-slate-200 hover:bg-rose-600 hover:text-white text-slate-800',
        'empty-state-icon\"><Route size={28} /></div>': 'empty-state-icon text-blue-500 bg-blue-50 border-blue-100\"><Route size={28} /></div>',
    }
    for k, v in rep.items():
        jsx = jsx.replace(k, v)
        
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
    print("Corporate Ocean theme applied successfully.")
