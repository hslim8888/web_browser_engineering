# Tree-based layout: there are two trees!
#      - children
#      - parent
# - Layout / box tree (which we will compute during layout)
#   - every node in the layout tree will have:
#      - x
#      - y
#      - width
#      - height
#      - children
#      - parent
#      - previous (previous sibling or None if first sibling)
#      - node (pointer into the corresponding node in the HTML tree)
import dataclasses
import socket
import ssl
import tkinter
import tkinter.font
from dataclasses import field
from typing import Dict, List, Optional, Union

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]


class DrawText:
    def __init__(self, x1, y1, text, font):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text=self.text,
            font=self.font,
            anchor='nw',
        )


class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width=0,
            fill=self.color,
        )


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        # css 추가 후 읽기 == 브라우저 내장 스타일 시트
        with open("browser.css") as f:
            self.default_style_sheet = CSSParser(f.read()).parse()

    def scrolldown(self, event):
        max_y = self.document.height - HEIGHT
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def scrollup(self, event):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll, self.canvas)

    def load(self, url):
        headers, body = request(url)
        # show(body)
        self.canvas.create_rectangle(10, 20, 400, 300)
        self.canvas.create_oval(100, 100, 150, 150)
        self.canvas.create_text(200, 150, text="Hi!")

        self.nodes = HTMLParser(body).parse()
        print_tree(self.nodes)

        rules = self.default_style_sheet.copy()  # css 파싱

        # <link rel="stylesheet" href="/main.css"> 이런 식으로 있는 스타일 시트 링크 저장하기
        links = [node.attributes["href"]
                 for node in tree_to_list(self.nodes, [])
                 if isinstance(node, Element)
                 and node.tag == "link"
                 and "href" in node.attributes
                 and node.attributes.get("rel") == "stylesheet"]
        for link in links:
            try:
                header, body = request(resolve_url(link, url))
            except Exception:
                continue
            rules.extend(CSSParser(body).file())

        # layout 이전에 style
        # rule - priority가 작은 순으로 정렬해야 함. 이후 큰 게 덮어쓰게.
        style(self.nodes, sorted(rules, key=cascade_priority))

        self.document = DocumentLayout(self.nodes)
        self.document.layout()

        self.display_list = []
        self.document.paint(self.display_list)
        # self.display_list contains the "answer" from paint:
        #  concatenation of all the display lists in order

        # self.display_list = InlineLayout(node).display_list
        self.draw()


def request(url):
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], f"Unknown scheme: {scheme}"

    host, path = url.split("/", 1)
    path = "/" + path

    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    # scheme == "http" ? 80 : 443
    port = 80 if scheme == "http" else 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    s.connect((host, port))

    s.send(bytes(f"GET {path} HTTP/1.0\r\n", encoding="utf8") +
           bytes(f"Host: {host}\r\n\r\n", encoding="utf8"))

    response = s.makefile("r", encoding="utf8", newline="\r\n")
    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", f"unexpected status {status}: {explanation}"

    headers = {}
    while (line := response.readline()) != "\r\n":
        header, value = line.split(":", 1)
        headers[header] = value.strip()

    body = response.read()
    s.close()

    return headers, body


# a token is either Text or Tag
@dataclasses.dataclass
class Text:
    text: str
    children: List['Node'] = field(default_factory=list)
    parent: Optional['Element'] = None

    def __repr__(self) -> str:
        return repr(self.text)


@dataclasses.dataclass
class Element:
    tag: str
    attributes: Dict[str, str]
    children: List['Node'] = field(default_factory=list)
    parent: Optional['Element'] = None

    def __repr__(self) -> str:
        return "<" + str(self.tag) + ">"


Node = Union[Text, Element]


def print_tree(node: Node, indent: int = 0) -> None:
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


@dataclasses.dataclass
class HTMLParser:
    body: str
    parser_stack: List[Element] = field(default_factory=list)

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:
                attributes[attrpair.lower()] = ""
        return tag, attributes

    def add_text(self, text: str) -> None:
        if text.isspace():
            return
        parent = self.parser_stack[-1]
        parent.children.append(Text(text, parent=parent))

    def add_tag(self, tag: str) -> None:
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return
        if tag.startswith("/"):
            # close tag
            if len(self.parser_stack) == 1:
                return
            node = self.parser_stack.pop()
            self.parser_stack[-1].children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.parser_stack[-1]
            node = Element(tag, attributes, parent=parent)
            parent.children.append(node)
        else:
            # open tag
            parent_opt = self.parser_stack[-1] if len(self.parser_stack) > 0 else None
            self.parser_stack.append(Element(tag, attributes, parent=parent_opt))

    def finish(self) -> Node:
        # close all open tags
        while len(self.parser_stack) > 1:
            node = self.parser_stack.pop()
            parent = self.parser_stack[-1]
            parent.children.append(node)
        return self.parser_stack.pop()

    def parse(self) -> Node:  # return a list of tokens
        text = ""
        inside_tag = False
        for c in self.body:
            if c == "<":
                inside_tag = True
                if text != "":
                    self.add_text(text)
                text = ""
            elif c == ">":
                inside_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not inside_tag and text != "":
            self.add_text(text)

        return self.finish()


BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]


def layout_mode(node):
    if isinstance(node, Text):
        return "inline"
    elif node.children:
        for child in node.children:
            if isinstance(child, Text):
                continue
            if child.tag in BLOCK_ELEMENTS:
                return "block"
        return "inline"
    else:
        return "block"


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        previous = None
        for html_child in self.node.children:
            if layout_mode(html_child) == "block":
                child = BlockLayout(html_child, self, previous)
            else:
                # it's inline
                child = InlineLayout(html_child, self, previous)
            previous = child
            self.children.append(child)
        # compute stuff "before" traversing down here
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous is None:
            self.y = self.parent.y
        else:
            self.y = self.previous.y + self.previous.height
        for child in self.children:
            child.layout()
        # compute stuff "after" traversing here
        self.height = sum(child.height for child in self.children)

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)

        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height + 2 * VSTEP

    def paint(self, display_out):
        self.children[0].paint(display_out)


class InlineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous is None:
            self.y = self.parent.y
        else:
            self.y = self.previous.y + self.previous.height

        self.cursor_x = self.x
        self.cursor_y = self.y
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.line = []
        self.display_list = []

        self.recurse(self.node)
        self.flush()

        self.height = self.cursor_y - self.y

    def text(self, tok):  # tok must be a Text token
        for word in tok.text.split():
            font = tkinter.font.Font(
                    family="Times",
                    size=self.size,
                    weight=self.weight,
                    slant=self.style,
                )
            w = font.measure(word)

            if self.cursor_x + w >= WIDTH - HSTEP:
                self.flush()

            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")

    # move the stuff in self.line to self.display_list
    def flush(self):
        if len(self.line) == 0:
            return

        # self.cursor_y += font.metrics("linespace") * 1.25
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        self.cursor_x = self.x
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"

    def recurse(self, node: Node) -> None:
        if isinstance(node, Text):
            self.text(node)
        else:
            self.open_tag(node.tag)
            for c in node.children:
                self.recurse(c)
            self.close_tag(node.tag)

    def paint(self, display_list):
        if isinstance(self.node, Element) and self.node.tag == "pre":
            bgcolor = self.node.style.get("background-color", "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
                display_list.append(rect)

        #     x2, y2 = self.x + self.width, self.y + self.height
        #     rect = DrawRect(self.x, self.y, x2, y2, "gray")
        #     display_list.append(rect)

        for x, y, word, font in self.display_list:
            display_list.append(DrawText(x, y, word, font))


class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0  # parser의 현재 위치

    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            # isalpha() - 특문이 있으면 거짓. 한글이나 영어(텍스트)만 있으면 참.
            # isalnum() - 텍스트 + 숫자면 참. 특문(공백 포함) 있으면 거짓.
            # 따라서 #-.% 이나 텍스트면 i를 더하는 것. 왜 #-.%는 되는거지?
            # 무튼 이렇게 단어를 self.s[start:self.i] 를 잘라내서 리턴하는 함수
            # 물론 진짜 css는 이것보다 더 복잡하다고.
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        assert self.i > start
        return self.s[start:self.i]

    def literal(self, literal):
        """
        property : value 일 때, prop 파싱이 끝난 후 :가 맞는지, 체크하는 거.
        아니면 assert 에러 냄
        맞으면 단순히 1 증가
        """
        assert self.i < len(self.s) and self.s[self.i] == literal
        self.i += 1

    def pair(self):
        """
        위의 함수를 이용해서 style attribute의 property / value를 파싱하는 거
        ex) <div style="background-color:lightblue"></div> 에서 "" 사이
        """
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()
        val = self.word()
        return prop.lower(), val

    def body(self):
        """
        { background-color: green; } > background-color: green 로 파싱된 걸
        dict 로 만들어 줌
        property / value 가 연속으로 있는 경우도 있나봄. 그게 또 ; 로 구분되고.
        CSS 에러 핸들링 생각하면 } 일 때 멈춰야
        """
        pairs = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val = self.pair()
                pairs[prop] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except AssertionError:  # literal에서 에러 나면,
                why = self.ignore_null([";", "}"])  # ; 나 } 만날 때까지 i 계속 증가.
                if why == ";":
                    self.literal(";")  # 현위치가 ;인 거 확인하고
                    self.whitespace()  # 1증가
                else:  # ; 가 없으면 그냥 문장 끝까지 달림.
                    break
        return pairs

    def selector(self):
        """
        아래에 만든 TagSelector, DescendantSelector 오브젝트를 이용
        CSS ex.
        1. pre { background-color: gray; }
        2. div div p { background-color: green; }
        """
        out = TagSelector(self.word().lower())  # tag == 1) div
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()  # 두 번째 div > 세 번째 p
            # 두 번째 인자로 무조건 TagSelector를 받고 이 안에만 tag가 있음. priority는 무조건 1
            out = DescendantSelector(out, TagSelector(tag.lower()))
            self.whitespace()
        return out

    def parse(self):
        """
        CSS 파일은 selector와 block의 연속이라고
        parse에도 에러 핸들링 해야
        div div p { background-color: green; }
        """
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()   # 최종적으로 p 가 div, div 둘 다 가지고 있는 형태
                self.literal("{")
                self.whitespace()
                body = self.body()  # background-color: green;
                self.literal("}")
                rules.append((selector, body))
            except AssertionError:
                why = self.ignore_null(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules

    def ignore_null(self, chars):
        """
        parse 에러가 나올 경우
        chars 가 나올 때까지 무시하고 i를 계속 증가... 여기선 세미콜론 ; -- js 에선 문장 마침표인데? html은??
        에러를 무시하게 해줘, 디버그가 힘들게 됨.

        하지만 브라우저는 여러 종류와 버전이 있고, 하나의 브라우저에서 되던 게 다른 곳에서는 안 될 수 있고...
        에러에 강건해야 함. 그래서 파서가 이해 못하는 건 무시하는 작전...이 쓰임
        """
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1


def style(node, rules):
    """
    각 style 필드에 위에서 파싱한 스타일 attr을 저장
    load 함수에서 call해서 쓸 거 > HTML 파싱 이후, layout 이전.
    CSSParser 에서 나온 rules 도 추가
    """
    node.style = {}

    # 이 부분 rules와 함께 추가됨
    for selector, body in rules:
        if not selector.matches(node): continue
        for property, value in body.items():
            node.style[property] = value

    if isinstance(node, Element) and "style" in node.attributes:
        # <div style="background-color:lightblue"></div> 이런 노드가 들어오면 파싱시작.
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value

    for child in node.children:
        style(child)




class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node):
        return isinstance(node, Element) and self.tag == node.tag


class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node):
        if not self.descendant.matches(node): return False
        while node.parent:
            if self.ancestor.matches(node.parent): return True
            node = node.parent
        return False


def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list


def resolve_url(url, current):
    """
    스타일 시트 url은 url이 생략된 경우도 많음. 그거 처리하기 위한 함수
    """
    if "://" in url:
        return url
    elif url.startswith("/"):
        scheme, hostpath = current.split("://", 1)
        host, oldpath = hostpath.split("/", 1)
        return scheme + "://" + host + url
    else:
        dir, _ = current.rsplit("/", 1)
        while url.startswith("../"):
            url = url[3:]
            if dir.count("/") == 2: continue
            dir, _ = dir.rsplit("/", 1)
        return dir + "/" + url


def cascade_priority(rule):
    selector, body = rule
    return selector.priority


def main(url: str) -> None:
    # CSSParser(url).body()
    Browser().load(url)
    tkinter.mainloop()


if __name__ == "__main__":
    url = 'https://browser.engineering/styles.html'
    main(url)
    # main(sys.argv[1])
