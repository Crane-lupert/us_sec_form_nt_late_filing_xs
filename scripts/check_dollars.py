with open('analysis/paper_v2_en.md', encoding='utf-8') as f:
    text = f.read()
for i, line in enumerate(text.split('\n'), 1):
    striped = line.replace('\\$', '')
    n = striped.count('$')
    if n % 2 != 0:
        print(f'line {i}: {n} dollar (odd) - {line[:120]}')
