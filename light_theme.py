import re
import codecs

def process_css(css):
    rep = {
        '#020617': '#f8fafc',
        'rgba(255, 255, 255, 0.06)': 'rgba(0, 0, 0, 0.06)',
        'rgba(255, 255, 255, 0.05)': 'rgba(0, 0, 0, 0.05)',
        'rgba(255, 255, 255, 0.07)': 'rgba(0, 0, 0, 0.07)',
        'rgba(255, 255, 255, 0.08)': 'rgba(0, 0, 0, 0.08)',
        'rgba(255, 255, 255, 0.1)': 'rgba(0, 0, 0, 0.1)',
        'rgba(255, 255, 255, 0.15)': 'rgba(0, 0, 0, 0.15)',
        'rgba(15, 23, 42, 0.85)': 'rgba(255, 255, 255, 0.85)',
        'rgba(15, 23, 42, 0.6)': 'rgba(255, 255, 255, 0.6)',
        'rgba(15, 23, 42, 0.5)': 'rgba(255, 255, 255, 0.6)',
        'rgba(30, 41, 59, 0.4)': 'rgba(255, 255, 255, 0.8)',
        'rgba(30, 41, 59, 0.65)': 'rgba(255, 255, 255, 1)',
        'rgba(30, 41, 59, 0.35)': 'rgba(255, 255, 255, 0.8)',
        'rgba(30, 41, 59, 0.5)': 'rgba(255, 255, 255, 1)',
        'rgba(2, 6, 23, 0.9)': 'rgba(255, 255, 255, 0.9)',
        'rgba(2, 6, 23, 0.5)': 'rgba(255, 255, 255, 0.6)',
        'rgba(2, 6, 23, 0.92)': 'rgba(255, 255, 255, 0.95)',
        'border-top-color: #fff': 'border-top-color: #6366f1',
        'box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4)': 'box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08)',
        'box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3)': 'box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05)',
        'box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6)': 'box-shadow: 0 25px 60px rgba(0, 0, 0, 0.15)'
    }
    for k, v in rep.items():
        css = css.replace(k, v)
    return css

def process_jsx(jsx):
    jsx = jsx.replace('https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json', 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json')
    
    # Specific targeted UI replacements to convert from dark to light mode cleanly
    rep = {
        'bg-slate-900': 'bg-slate-50',
        'bg-slate-800': 'bg-white',
        'bg-slate-700': 'bg-slate-100',
        'border-slate-700': 'border-slate-200',
        'border-white/5': 'border-black/5',
        'text-slate-300': 'text-slate-700',
        'text-slate-400': 'text-slate-600',
        'text-slate-200': 'text-slate-800',

        # specific texts
        'text-white flex-col': 'text-slate-900 flex-col',
        'text-white leading-none': 'text-slate-900 leading-none',
        'text-white font-medium truncate': 'text-slate-900 font-medium truncate',
        'text-base font-semibold text-white': 'text-base font-semibold text-slate-900',
        'text-2xl font-bold text-white': 'text-2xl font-bold text-slate-900',
        'text-sm font-semibold text-white': 'text-sm font-semibold text-slate-900',
        'span className="text-white font-semibold"': 'span className="text-slate-900 font-semibold"',
        'bg-slate-600/60': 'bg-slate-200',
        
        # fix button text contrasts that were made slate when it shouldn't
        'hover:text-rose-600 text-white': 'hover:text-rose-600 text-slate-700',
        
        # In risk panel, white texts
        'text-white text-xs font-bold': 'text-white text-xs font-bold', # Map risk node marker
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
    print("Theme applied successfully.")
