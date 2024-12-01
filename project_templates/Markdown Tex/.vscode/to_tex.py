import re
import os


def convert_refs(text):
    # Регулярное выражение для поиска комментариев с изображениями
    img_pattern = r'<!--\s*(img\/.*\.(?:png|jpg|jpeg|gif))\s*-->'

    # Регулярное выражение для поиска комментариев с таблицами
    table_pattern = r'<!--\s*\|.*?\|.*?-->'

    # Регулярное выражение для поиска комментариев с $ ... $
    equation_pattern = r'<!--\s*\$\$(.*?)\$\$\s*-->'

    # Замена комментариев на LaTeX команды \cref для изображений
    def img_replacement(match):
        image_path = match.group(1)
        # Создаем метку для изображения
        label = 'fig:' + \
            image_path.replace('/', '-').replace('.',
                                                 '-').replace(';', ',fig:')
        return f'\\cref{{{label}}}'

    # Замена комментариев на LaTeX команды для таблиц
    def table_replacement(match):
        # Получаем содержимое таблицы
        table_content = match.group(0)
        # Удаляем начальные и конечные вертикальные черты и пробелы
        cleaned_content = table_content.strip('<!-- ').strip(' -->').strip()
        # Создаем метку для таблицы, чтобы метку для нескольких таблиц, разделяй при помощи ";"
        label = 'tab:' + \
            re.sub(r'\s+', '-', cleaned_content.replace('|',
                   '-').replace('\\', '-').replace(';', ',tab:'))
        return f'\\cref{{{label}}}'

    # Замена комментариев с выражением на LaTeX команды для cref
    def equation_replacement(match):
        equation_content = match.group(1)
        # Создаем метку для cref
        label = 'eq:' + \
            re.sub(r'\s+', '-', equation_content.replace('\\', '-')
                   ).replace('$$;$$', ',eq:')
        return f'\\cref{{{label}}}'

    # Заменяем все найденные комментарии на LaTeX команды \ref
    text = re.sub(img_pattern, img_replacement, text)
    text = re.sub(table_pattern, table_replacement,
                  text)  # Заменяем на метку таблицы
    text = re.sub(equation_pattern, equation_replacement,
                  text, flags=re.DOTALL)  # Заменяем на метку выражения

    return text


def convert_code_blocks(text):
    # Заменяем блоки кода в формате Markdown на LaTeX
    new_text = re.sub(
        r'```(.*?)```', r'\\begin{lstlisting}\1\\end{lstlisting}', text, flags=re.DOTALL)
    # Добавляем комментарий <!-- ignore --> после каждой строки внутри lstlisting
    new_text = re.sub(r'(\\begin{lstlisting})(.*?)(\\end{lstlisting})',
                      lambda m: f"{m.group(1)}{'\n'+''.join(list(m.group(2))[1:]).replace(
                          '\n', '<!-- ignore -->\n')}{m.group(3)}",
                      new_text, flags=re.DOTALL)
    return new_text


def markdown_enumerate_to_latex(text):
    # Регулярное выражение для поиска нумерованных списков в Markdown
    pattern = r'^(\d+)\. (.*)$'
    lines = text.split('\n')
    latex_lines = []
    in_list = False
    for line in lines:
        match = re.match(pattern, line)
        if match:
            # Если нашли нумерованный список, преобразуем его в список enumerate LaTeX
            if not in_list:
                latex_lines.append('\\begin{enumerate}[left=\parindent]')
                in_list = True
            num, item = match.groups()
            latex_lines.append(f'   \\item[{num}.] {item}')
        else:
            if in_list:
                latex_lines.append('\\end{enumerate}')
                in_list = False
            latex_lines.append(line)
    if in_list:
        latex_lines.append('\\end{enumerate}')
    return '\n'.join(latex_lines)


def markdown_list_to_latex(text):
    """
    Трансформирует ненумерованные списки формата markdown в формат latex
    """
    def latex_list(match):
        items = [
            f'    \\item[--] {item[2:].strip()}' for item in match.split('\n')][:-1]
        return '\\begin{itemize}[left=\parindent]\n' + '\n'.join(items) + '\n\\end{itemize}\n'
    # шаблон для поиска ненумерованного списка markdown
    pattern = r'((^- .*?\n)+)'
    return re.sub(pattern, lambda match: latex_list(match.group(0)), text, flags=re.MULTILINE)


def convert_italic_and_bold_text(text):
    new_text = re.sub(
        r'\*\*([^*]+)\*\*(?!.*<!-- ignore -->)', r'\\textbf{\1}', text)
    new_text = re.sub(r'\*([^*]+)\*(?!.*<!-- ignore -->)',
                      r'\\textit{\1}', new_text)
    new_text = re.sub(r'<!-- ignore -->', '', new_text)
    return new_text


def extract_title_from_comment(text):
    pattern = r'<!--\s*Title:\s*(.+?)\s*-->'
    match = re.search(pattern, text)

    if match:
        title = match.group(1)
        text_without_comment = text.replace(f"{match.group(0)}\n", '')
        return text_without_comment, title
    else:
        return text, None


def extract_author_from_comment(text):
    pattern = r'<!--\s*Author:\s*(.+?)\s*-->'
    match = re.search(pattern, text)

    if match:
        author = match.group(1)
        text_without_comment = text.replace(f"{match.group(0)}\n", '')
        return text_without_comment, author
    else:
        return text, None


def convert_latex_math(text):
    text = re.sub(r'\\\$', r'\\dollar', text)

    def equation_replacement(match):
        equation_content = match.group(1)
        # Заменяем пробелы на дефисы в содержимом уравнения
        cleaned_equation = re.sub(
            r'\s+', '-', equation_content.replace('\\', '-'))
        return f'\\[{equation_content}\\label{{eq:{cleaned_equation}}}\\]'

    text = re.sub(r'\$\$(.*?)\$\$', equation_replacement,
                  text, flags=re.DOTALL)
    text = re.sub(r'\$(.*?)\$', r'\\(\1\\)', text)
    text = re.sub(r'\\dollar', r'\\$', text)
    return text


def transform_markdown_to_latex_comments(text):
    # Define a regular expression pattern to match Markdown comments
    pattern = r'<!--(.*?)-->'

    # Use the re.DOTALL flag to match newlines within the comments
    matches = re.findall(pattern, text, re.DOTALL)

    # Transform the Markdown comments to LaTeX format
    latex_comments = ['\n'.join(
        ['% ' + line.strip() for line in comment.splitlines()]) for comment in matches]

    # Replace the Markdown comments with the LaTeX comments
    transformed_text = text
    for i, comment in enumerate(matches):
        transformed_text = transformed_text.replace(
            f'<!--{comment}-->', latex_comments[i])

    return transformed_text


def convert_markdown_to_latex_sections(text):
    # Define regular expressions to search for sections in Markdown
    pattern = r'^(#+)\s*(.+)$'

    # Dictionary to map Markdown heading levels to LaTeX commands
    level_map = {
        '#': '\\chapter{',
        '##': '\\section{',
        '###': '\\subsection{',
        '####': '\\subsubsection{'
    }

    # Initialize the resulting text
    result = ''

    # Split the text into lines
    lines = text.split('\n')

    # Process each line
    for line in lines:
        match = re.match(pattern, line)
        if match:
            level = match.group(1)
            title = match.group(2)
            result += f"{level_map[level]}{title}{"}"}\n"
        else:
            result += line + '\n'

    return result


def convert_images(text):
    pattern = r'\!\[\]\((img\/[\w\-]+\.(?:png|jpg|jpeg|gif))\)\n\n([^\n]*)'

    def replacement(match):
        image_path = match.group(1)
        caption_text = match.group(2)
        # Заменяем символы для создания метки
        label = 'fig:' + image_path.replace('/', '-').replace('.', '-')
        return (f'\\begin{{figure}}[H]\n'
                f'    \\centering\n'
                f'    \\includegraphics*[width=0.8\\linewidth]{{{
                    image_path}}}\n'
                f'    \\caption{{{caption_text}}}\n'
                f'    \\label{{{label}}}\n'
                f'\\end{{figure}}')

    replaced_image = re.sub(pattern, replacement, text)
    return replaced_image


def get_first_letter(string):
    if string:
        return string[0]
    else:
        return ""


def markdown_to_latex_table(text):
    # Split the text into lines
    lines = text.split('\n')

    # Initialize an empty list to store the LaTeX table
    latex_table = []

    # Initialize an empty list to store the output text
    output_text = []

    # Iterate through the lines
    i = 0
    while i < len(lines):
        # Check if the current line is a Markdown table
        if '|' in lines[i] and get_first_letter(lines[i]) == '|':
            # Get the table header
            header = lines[i].strip().split('|')[1:-1]
            header = ["\\textbf{" + h.strip() + "}" for h in header]

            # Get the table alignment
            alignment = lines[i+1].strip().split('|')[1:-1]
            alignment = [a.strip() for a in alignment]
            alignment = [re.sub(r'-+', 'Z', a) for a in alignment]

            # Get the table rows
            rows = []
            i += 2
            while i < len(lines) and '|' in lines[i]:
                row = lines[i].strip().split('|')[1:-1]
                row = [r.strip() for r in row]
                rows.append(row)
                i += 1

            # Get the caption text
            i += 1
            caption_text = lines[i]

            # Convert the Markdown table to a LaTeX table
            latex_table.append(r'\begin{table}[H]')
            latex_table.append(r'    \centering')
            latex_table.append(
                r'    \begin{tabularx}{0.9\textwidth}{|' + '|'.join(alignment) + r'|} \hline')
            latex_table.append('        ' + ' & '.join(header) + r' \\ \hline')
            for row in rows:
                latex_table.append(
                    '        ' + ' & '.join(row) + r' \\ \hline')
            latex_table.append(r'    \end{tabularx}')
            latex_table.append(r'    \caption{' + caption_text + '}')
            latex_table.append(
                r'    \label{' + re.sub(r'\s+', '-', 'tab:' + lines[i - len(rows) - 3].replace('|', '-')) + '}')
            latex_table.append(r'\end{table}')

            # Add the LaTeX table to the output text
            output_text.extend(latex_table)
            latex_table = []

            i += 1
        else:
            output_text.append(lines[i])
            i += 1

    # Join the output text lines into a single string
    output_text = '\n'.join(output_text)

    return output_text


def convert_links(text):
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    replacement = r'\\href{\2}{\1}'
    return re.sub(pattern, replacement, text)


def create_latex_file(markdown_file):
    with open(markdown_file, 'r', encoding="utf-8") as file:
        file_content = file.read()

    formatted_file_content, title = extract_title_from_comment(file_content)
    formatted_file_content, author = extract_author_from_comment(
        formatted_file_content)
    formatted_file_content = convert_refs(
        formatted_file_content)
    formatted_file_content = convert_code_blocks(
        formatted_file_content)
    formatted_file_content = convert_italic_and_bold_text(
        formatted_file_content)
    formatted_file_content = markdown_list_to_latex(
        formatted_file_content)
    formatted_file_content = markdown_enumerate_to_latex(
        formatted_file_content)
    formatted_file_content = convert_latex_math(formatted_file_content)
    formatted_file_content = convert_images(formatted_file_content)
    formatted_file_content = markdown_to_latex_table(formatted_file_content)
    formatted_file_content = transform_markdown_to_latex_comments(
        formatted_file_content)
    formatted_file_content = convert_markdown_to_latex_sections(
        formatted_file_content)
    formatted_file_content = convert_links(formatted_file_content)

    latex_template = f"""% !TEX program = xelatex
\\documentclass[a4paper]{{article}}
\\usepackage[fontsize=14pt]{{fontsize}}
\\usepackage[english, russian]{{babel}}
\\usepackage{{amsmath}}
\\usepackage{{xcolor}}
\\usepackage{{accsupp}}
\\usepackage{{listings}}
\\usepackage{{float}}
\\usepackage[unicode, colorlinks=true, linkcolor=blue]{{hyperref}}
\\usepackage{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{latexsym}}
\\usepackage{{amssymb}}
\\usepackage{{indentfirst}}
\\usepackage{{tikz}}
\\usepackage{{pgfplots}}
\\usepackage{{bookmark}}
\\usepackage{{multicol}}
\\usepackage{{caption}}
\\usepackage{{fontspec}}
\\usepackage{{unicode-math}}
\\usepackage{{titlesec}}
\\usepackage{{tocloft}}
\\usepackage{{tabularx}}
\\usepackage{{enumitem}}
\\usepackage[labelsep=endash]{{caption}}
\\usepackage{{datetime2}}
\\usepackage{{cleveref}}
% Uncomment below to enable text style math
% \\usepackage{{mathastext}}

\\crefformat{{figure}}{{(см. рис. #2#1#3)}}
\\crefmultiformat{{figure}}{{(см. рис. #2#1#3}}{{ и #1)}}{{, #1}}{{ и #1)}}
\\crefformat{{table}}{{(см. табл. #2#1#3)}}
\\crefmultiformat{{table}}{{(см. табл. #2#1#3}}{{ и #1)}}{{, #1}}{{ и #1)}}
\\crefformat{{equation}}{{(см. (#2#1#3))}}
\\crefmultiformat{{equation}}{{(см. (#2#1#3)}}{{ и (#1))}}{{, (#1)}}{{ и (#1))}}

\\DTMnewdatestyle{{monthyear}}{{%
    % ##1 = year, ##2 = month, ##3 = day
    \\renewcommand*{{\\DTMdisplaydate}}[4]{{\\DTMenglishmonthname{{##2}} ##1}}%
    \\renewcommand*{{\\DTMDisplaydate}}{{\\DTMdisplaydate}}%
}}

\\addto\\captionsrussian{{\\renewcommand{{\\figurename}}{{Рисунок}}}}

\\setlength\\parindent{{15mm}}

\\renewcommand{{\\cftsecfont}}{{\\normalfont}}
\\renewcommand{{\\cftsecpagefont}}{{\\normalfont}}

\\setlength{{\\cftsecindent}}{{0pt}}
\\setlength{{\\cftsubsecindent}}{{0pt}}
\\setlength{{\\cftsubsubsecindent}}{{0pt}}

\\newcommand{{\\HY}}{{\\hyphenpenalty=25\\exhyphenpenalty=25}}
\\newcolumntype{{Z}}{{>{{\\HY\\arraybackslash\\hspace{{0pt}}}}X}}
\\newcolumntype{{M}}{{>{{\\HY\\RaggedRight\\arraybackslash\\hspace{{0pt}}}}c}}
\\newcolumntype{{L}}{{>{{\\HY\\RaggedRight\\arraybackslash\\hspace{{0pt}}}}l}}

\\titleformat{{\\section}}{{\\large\\scshape\\color{{darkgray}}}}{{\\hspace*{{-4.5em}}\\rule[-1.35mm]{{4.5em}}{{1.25em}}{{\\color{{white}}\\hspace{{-1cm}}\\large\\scshape\\thesection\\hspace{{5pt}}}}}}{{22pt}}{{}}
% \\titleformat{{\\section}}{{\\large\\scshape}}{{\\thesection}}{{10pt}}{{}}
\\titleformat{{\\subsection}}{{\\large\\scshape\\color{{gray}}}}{{\\hspace*{{-4.5em}}\\rule[-1.35mm]{{4.5em}}{{1.25em}}{{\\color{{white}}\\hspace{{-1cm}}\\large\\scshape\\thesubsection\\hspace{{5pt}}}}}}{{10pt}}{{}}
% \\titleformat{{\\subsection}}{{\\large\\scshape}}{{\\thesubsection}}{{10pt}}{{}}
\\titleformat{{\\subsubsection}}{{\\large\\scshape\\color{{gray}}}}{{\\thesubsubsection}}{{10pt}}{{}}

\\renewcommand{{\\cftsecleader}}{{\\cftdotfill{{\\cftdotsep}}}}

\\newcommand{{\\chapter}}[1]{{%
    \\newpage%
    \\begin{{center}}%
        \\phantomsection\\bfseries\\large\\scshape\\uppercase{{#1}}%
    \\end{{center}}%
    \\addcontentsline{{toc}}{{section}}{{#1}}%
}}

\\AtBeginDocument{{%
    \\renewcommand{{\\cfttoctitlefont}}{{}}%
    \\renewcommand\\contentsname{{%
        \\begin{{center}}%
            \\bfseries\\large\\scshape\\color{{black}}\\uppercase{{Содержание}}%
        \\end{{center}}%
        \\vspace{{-0.5cm}}%
    }}%
}}

% Uncomment this two to make every row stretch
% \\hyphenpenalty=10000
% \\tolerance=1
\\hbadness=10000
\\emergencystretch=\\maxdimen

\\renewcommand{{\\cftsecfont}}{{\\fontspec{{Times New Roman}}}}
\\renewcommand{{\\cftsubsecfont}}{{\\fontspec{{Times New Roman}}}}
\\renewcommand{{\\cftsubsubsecfont}}{{\\fontspec{{Times New Roman}}}}

\\setmainfont{{Times New Roman}}
\\linespread{{1.5}}

\\DeclareSymbolFont{{letters}}{{\\encodingdefault}}{{\\rmdefault}}{{m}}{{it}}

\\pgfplotsset{{compat=1.7}}

\\definecolor{{codegreen}}{{rgb}}{{0,0.6,0}}
\\definecolor{{codegray}}{{rgb}}{{0.5,0.5,0.5}}
\\definecolor{{codepurple}}{{rgb}}{{0.58,0,0.82}}
\\definecolor{{backcolour}}{{rgb}}{{0.95,0.95,0.92}}
\\newcommand{{\\noncopynumber}}[1]{{%
    \\BeginAccSupp{{method=escape,ActualText={{}}}}%
    #1%
    \\EndAccSupp{{}}%
}}
\\lstdefinestyle{{mycodestyle}}{{
    frame=single,
    backgroundcolor=\\color{{backcolour}},
    commentstyle=\\color{{codegreen}},
    keywordstyle=\\color{{blue}},
    numbers=left,
    numberstyle=\\color{{codegray}},
    breaklines=true,
    basicstyle=\\ttfamily,
    breakatwhitespace=false,
    captionpos=b,
    keepspaces=true,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    columns=fullflexible,
    numberstyle=\\noncopynumber,
    language=C++,
    alsolanguage=PHP
}}
\\lstset{{style=mycodestyle}}
% \\begin{{lstlisting}}
% #include <iostream>

% int main() {{
%     std::cout << "Hello, world!" << std::endl;
%     return 0;
% }}
% \\end{{lstlisting}}

\\geometry{{left=30mm}}
\\geometry{{right=15mm}}
\\geometry{{top=20mm}}
\\geometry{{bottom=20mm}}

\\graphicspath{{{{img/}}}}

\\def\\[#1\\]{{\\begin{{equation}}\\begin{{gathered}}#1\\end{{gathered}}\\end{{equation}}}}

\\begin{{document}}
\\begin{{titlepage}}
    \\centering
    \\par
    {{\\scshape ITMO University\\par}}
    \\vspace{{80mm}}
    {{\\Large\\bfseries\\scshape {title if title is not None else "Название"}\\par}}
    \\vspace{{20mm}}
    {{\\scshape {author if author is not None else "Кербер Егор"}\\par}}
    \\vfill
    {{\\scshape\\DTMsetdatestyle{{monthyear}}\\today\\par}}
\\end{{titlepage}}

\\setcounter{{page}}{{2}}
\\tableofcontents
\\newpage

{formatted_file_content}

\\end{{document}}"""

    with open(f"{os.path.splitext(os.path.basename(markdown_file))[0]}.tex", "w", encoding="utf-8") as f:
        f.write(latex_template)


def find_markdown_files():
    markdown_files = []
    current_dir = os.getcwd()
    for filename in os.listdir(current_dir):
        if filename.endswith(".md"):
            markdown_files.append(filename)
    return markdown_files


markdown_files = find_markdown_files()

if markdown_files:
    create_latex_file(markdown_files[0])
