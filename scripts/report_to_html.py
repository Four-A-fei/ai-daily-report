#!/usr/bin/env python3
"""Convert AI daily report markdown to styled HTML page with clickable links."""
import sys, re, json, os
from datetime import datetime

def md_to_html(md_text):
    date = datetime.now().strftime('%Y-%m-%d')
    
    with open('/Users/yuanshuzhihui/.qclaw/workspace/daily-report-template.html', 'r') as f:
        template = f.read()
    
    highlights = ''
    categories = ''
    github = ''
    insights = ''
    chicken_soup = '今天也要加油鸭！'
    source_stats = ''
    
    lines = md_text.split('\n')
    current_section = None
    current_cat = None
    cat_items = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('## 今日重点'):
            current_section = 'highlights'
            i += 1; continue
        elif line.startswith('## 分类新闻'):
            current_section = 'categories'
            i += 1; continue
        elif line.startswith('## GitHub热门项目'):
            current_section = 'github'
            i += 1; continue
        elif line.startswith('## 创业与投资洞察'):
            current_section = 'insights'
            i += 1; continue
        elif line.startswith('## 毒鸡汤') or (line.startswith('🐔') and current_section not in ('highlights', 'categories', 'github', 'insights')):
            current_section = 'chicken'
            if line.startswith('🐔'):
                chicken_soup = line.lstrip('🐔 ').strip()
                i += 1; continue
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                chicken_soup = lines[i].strip().lstrip('🐔 ').strip()
            i += 1; continue
        elif line.startswith('## 信源统计'):
            current_section = 'stats'
            i += 1
            stats_lines = []
            while i < len(lines):
                if lines[i].strip():
                    stats_lines.append(lines[i].strip())
                i += 1
            source_stats = ' '.join(stats_lines)
            continue
        
        # === HIGHLIGHTS ===
        if current_section == 'highlights' and line.startswith('###'):
            m = re.match(r'###\s*\d+\.\s*【(.+?)】(.+?)(✅|⚠️)?\s*$', line)
            if m:
                cat, title, badge = m.group(1), m.group(2).strip(), m.group(3) or ''
                tag_class = get_tag_class(cat)
                badge_html = '<span class="badge-verified">✅确定</span>' if '✅' in badge else '<span class="badge-uncertain">⚠️待确认</span>'
                content_parts = []
                source = ''
                link = ''
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('###') and not lines[i].strip().startswith('## '):
                    l = lines[i].strip()
                    if l.startswith('•'):
                        content_parts.append(f'<p>{l}</p>')
                    elif l.startswith('信源：') or l.startswith('信源:'):
                        source_text = re.sub(r'^信源[：:]', '', l).strip().rstrip('•').strip()
                        url_match = re.search(r'(https?://\S+)', source_text)
                        if url_match:
                            link = url_match.group(1)
                        source = source_text
                    i += 1
                
                if link:
                    highlights += f'''<a class="highlight-card" href="{link}" target="_blank" rel="noopener">
  <span class="tag {tag_class}">{cat}</span>{badge_html}<span class="arrow">→</span>
  <div class="title">{title}</div>
  <div class="content">{"".join(content_parts)}</div>
  <div class="source">信源：{source}</div>
</a>\n'''
                else:
                    highlights += f'''<div class="highlight-card">
  <span class="tag {tag_class}">{cat}</span>{badge_html}
  <div class="title">{title}</div>
  <div class="content">{"".join(content_parts)}</div>
  <div class="source">信源：{source}</div>
</div>\n'''
                continue
        
        # === CATEGORIES ===
        if current_section == 'categories' and line.startswith('###'):
            if current_cat and cat_items:
                categories += render_category(current_cat, cat_items)
            m = re.match(r'###\s*(.+)', line)
            current_cat = m.group(1).strip() if m else '其他'
            cat_items = []
            i += 1; continue
        
        if current_section == 'categories' and line and not line.startswith('#'):
            # 去掉 ** 粗体和 • 符号
            title = re.sub(r'\*\*(.*?)\*\*', r'\1', line).strip().lstrip('•').strip()
            badge = '✅' if '✅' in line else ('⚠️' if '⚠️' in line else '')
            desc = ''
            source = ''
            link = ''
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('###') and not lines[i].strip().startswith('## '):
                l = lines[i].strip()
                if l.startswith('信源：') or l.startswith('信源:'):
                    source_text = re.sub(r'^信源[：:]', '', l).strip().rstrip('•').strip()
                    url_match = re.search(r'(https?://\S+)', source_text)
                    if url_match:
                        link = url_match.group(1)
                    source = source_text
                elif l.startswith('•'):
                    desc += l[1:].strip() + ' '
                else:
                    desc += l + ' '
                i += 1
            cat_items.append({'title': title, 'desc': desc.strip(), 'source': source, 'badge': badge, 'link': link})
            continue
        
        # === GITHUB ===
        if current_section == 'github' and line.startswith('###'):
            # 格式：### 1. Significant-Gravitas/AutoGPT
            m = re.match(r'###\s*\d+\.\s*(.+)', line)
            name = m.group(1).strip() if m else line.replace('###', '').strip()
            heat = ''; desc = ''; link = ''
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('###') and not lines[i].strip().startswith('## '):
                pl = lines[i].strip()
                # 去掉粗体标记 **
                pl_clean = re.sub(r'\*\*(.*?)\*\*', r'\1', pl)
                
                if '热度' in pl_clean and ('：' in pl_clean or ':' in pl_clean):
                    heat = re.sub(r'^\*\*热度[：:]\*\*\s*', '', pl).strip()
                elif '简介' in pl_clean and ('：' in pl_clean or ':' in pl_clean):
                    desc = re.sub(r'^\*\*简介[：:]\*\*\s*', '', pl).strip()
                elif '链接' in pl_clean and ('：' in pl_clean or ':' in pl_clean):
                    link = re.sub(r'^\*\*链接[：:]\*\*\s*', '', pl).strip()
                elif pl.startswith('http'):
                    link = pl
                i += 1
            
            href = f'href="{link}"' if link else ''
            target = 'target="_blank" rel="noopener"' if link else ''
            tag = 'a' if link else 'div'
            
            github += f'''<{tag} class="gh-card" {href} {target}>
  <div class="name">{name}</div><span class="arrow">→</span>
  <div class="heat">🔥 {heat}</div>
  <div class="desc">{desc}</div>
</{tag}>\n'''
            continue
        
        # === INSIGHTS ===
        if current_section == 'insights' and line.startswith('### 方向'):
            m = re.match(r'###\s*方向[一二三][：:]?\s*(.+)', line)
            dir_title = m.group(1).strip() if m else line.replace('###', '').strip()
            opp = ''; drive = ''; potential = ''; entry = ''; risk = ''
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('### 方向') and not lines[i].strip().startswith('## '):
                l = lines[i].strip()
                if l.startswith('**核心机会：**'):
                    opp = l.replace('**核心机会：**', '').strip()
                elif l.startswith('**市场潜力：**'):
                    potential = l.replace('**市场潜力：**', '').strip()
                elif l.startswith('**建议切入点：**'):
                    entry = l.replace('**建议切入点：**', '').strip()
                elif l.startswith('**风险提示：**'):
                    risk = l.replace('**风险提示：**', '').strip()
                elif l.startswith('**驱动因素：**'):
                    pass
                elif l.startswith('•') and not drive:
                    drive = l[1:].strip()
                elif l.startswith('•'):
                    drive += '；' + l[1:].strip()
                i += 1
            
            insights += f'''<div class="insight-card">
  <div class="title">🎯 {dir_title}</div>
  <div class="field"><strong>核心机会：</strong><span>{opp}</span></div>
  <div class="field"><strong>驱动因素：</strong><span>{drive}</span></div>
  <div class="field"><strong>市场潜力：</strong><span>{potential}</span></div>
  <div class="field"><strong>建议切入点：</strong><span>{entry}</span></div>
  <div class="field risk"><strong>⚠️ 风险提示：</strong><span>{risk}</span></div>
</div>\n'''
            continue
        
        i += 1
    
    if current_cat and cat_items:
        categories += render_category(current_cat, cat_items)
    
    html = template.replace('{{DATE}}', date)
    html = html.replace('{{HIGHLIGHTS}}', highlights)
    html = html.replace('{{CATEGORIES}}', categories)
    html = html.replace('{{GITHUB}}', github)
    html = html.replace('{{INSIGHTS}}', insights)
    html = html.replace('{{CHICKEN_SOUP}}', chicken_soup)
    html = html.replace('{{SOURCE_STATS}}', source_stats)
    
    return html, date

def get_tag_class(cat):
    return {
        '大语言模型': 'tag-llm',
        '多模态AI': 'tag-multimodal',
        '芯片与硬件': 'tag-chip',
        '机器人技术': 'tag-robot',
        'AI安全与伦理': 'tag-safety',
        '传统行业+AI': 'tag-industry',
    }.get(cat, 'tag-llm')

def render_category(cat_name, items):
    """Render category section with card style (same as highlights)."""
    cat_icon = {
        '大语言模型': '🧠', '多模态AI': '🎨', '芯片与硬件': '🔧',
        '机器人技术': '🤖', 'AI安全与伦理': '🛡️', '传统行业+AI': '🏭',
    }.get(cat_name, '📰')
    
    tag_class = get_tag_class(cat_name)
    
    html = f'<div class="cat-section"><div class="cat-title"><span class="tag {tag_class}">{cat_icon}</span> {cat_name}</div>\n'
    for item in items:
        badge_html = '<span class="badge-verified">✅确定</span>' if item['badge'] == '✅' else ('<span class="badge-uncertain">⚠️待确认</span>' if item['badge'] == '⚠️' else '')
        link = item.get('link', '')
        
        title = item['title']
        desc = item['desc']
        source = item['source']
        
        if link:
            html += f'''<a class="cat-item" href="{link}" target="_blank" rel="noopener">
  <div class="title">{title}</div><span class="arrow">→</span>
  <div class="desc">{desc}</div>
  <div class="source">信源：{source}</div>
</a>\n'''
        else:
            html += f'''<div class="cat-item">
  <div class="title">{title}</div>
  <div class="desc">{desc}</div>
  <div class="source">信源：{source}</div>
</div>\n'''
    html += '</div>\n'
    return html

def generate_index(dates, latest_date):
    """Generate index.html listing all reports."""
    items = ''
    for d in sorted(dates, reverse=True):
        label = d
        # Format: 2026-05-25 -> 5月25日
        try:
            dt = datetime.strptime(d, '%Y-%m-%d')
            weekday = ['周一','周二','周三','周四','周五','周六','周日'][dt.weekday()]
            label = f'{dt.month}月{dt.day}日 {weekday}'
        except:
            pass
        latest_badge = ' 🆕' if d == latest_date else ''
        items += f'''<a class="news-item" href="{d}.html" style="text-decoration:none;color:inherit;">
  <div class="title" style="font-size:16px;">📰 {label}{latest_badge}</div><span class="arrow">→</span>
</a>\n'''
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI科技每日简报</title>
<style>
  :root, :root[data-theme="light"] {{
    --bg: #f5f5f7;
    --card: #ffffff;
    --border: #e5e5e5;
    --text: #1a1a1a;
    --muted: #6b6b6b;
    --accent: #4f46e5;
    --shadow: rgba(0,0,0,0.06);
  }}
  :root[data-theme="dark"] {{
    --bg: #0a0a0f;
    --card: #13131a;
    --border: #1e1e2e;
    --text: #e4e4e7;
    --muted: #71717a;
    --accent: #6366f1;
    --shadow: rgba(0,0,0,0.3);
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 20px 16px;
    max-width: 760px;
    margin: 0 auto;
  }}
  .header {{
    text-align: center;
    padding: 40px 0 30px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
  }}
  .header .logo {{ font-size: 40px; margin-bottom: 8px; }}
  .header h1 {{
    font-size: 24px;
    background: linear-gradient(135deg, var(--accent), #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
  }}
  .header .desc {{ color: var(--muted); font-size: 14px; }}
  .news-item {{
    display: block;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    transition: border-color 0.2s, box-shadow 0.2s;
    cursor: pointer;
  }}
  .news-item:hover {{
    border-color: var(--accent);
    box-shadow: 0 4px 12px var(--shadow);
  }}
  .news-item .title {{
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
  }}
  .news-item .arrow {{
    float: right;
    color: var(--muted);
    font-size: 14px;
    margin-top: 2px;
    transition: color 0.2s, transform 0.2s;
  }}
  .news-item:hover .arrow {{
    color: var(--accent);
    transform: translateX(3px);
  }}
  .footer {{
    text-align: center;
    padding: 20px;
    color: var(--muted);
    font-size: 12px;
    border-top: 1px solid var(--border);
    margin-top: 32px;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="logo">🤖</div>
    <h1>AI 科技每日简报</h1>
    <div class="desc">历史报告归档</div>
  </div>
  <div class="list">
    {items}
  </div>
  <div class="footer">
    Powered by QClaw AI
  </div>
</body>
</html>'''

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 report_to_html.py <input.md> <output_dir>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html_content, date_str = md_to_html(md_content)
    
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f'{date_str}.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Report saved to {output_file}")
    
    # Update index.html
    dates = []
    if os.path.exists(os.path.join(output_dir, 'dates.json')):
        with open(os.path.join(output_dir, 'dates.json'), 'r') as f:
            dates = json.load(f)
    
    if date_str not in dates:
        dates.append(date_str)
    
    with open(os.path.join(output_dir, 'dates.json'), 'w') as f:
        json.dump(dates, f)
    
    index_html = generate_index(dates, date_str)
    index_file = os.path.join(output_dir, 'index.html')
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"Index saved to {index_file}")
