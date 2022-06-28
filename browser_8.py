import dataclasses
from dataclasses import field
import tkinter
import tkinter.font
import socket
import ssl
import sys
import urllib.parse

from typing import Dict, List, Literal, Optional, Union


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]


class DrawText:
    def __init__(self, x1, y1, text, font, color):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.color = color
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text=self.text,
            font=self.font,
            anchor='nw',
            fill=self.color,
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

DrawCmd = Union[DrawText, DrawRect]


def tree_to_list(tree, list):
    list.append(tree)
    for child in tree.children:
        tree_to_list(child, list)
    return list


def resolve_url(url, current):
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
            if dir.count("/") == 2:
                continue
            dir, _ = dir.rsplit("/", 1)
        return dir + "/" + url


class Tab:
    def __init__(self):
        self.scroll = 0
        with open('browser.css') as f:
            self.default_style_sheet = CSSParser(f.read()).file()
        self.url = None
        self.history = []
        self.focus: Optional[Element] = None

    def click(self, x, y):
        # transform into page space coordinates
        y += self.scroll

        objs = [obj for obj in tree_to_list(self.document, [])
                if obj.x <= x < obj.x + obj.width
                and obj.y <= y < obj.y + obj.height]
        if not objs:
            return
        elt = objs[-1].node

        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                href = elt.attributes["href"]
                url = resolve_url(href, self.url)
                return self.load(url)
            elif elt.tag == "input":
                self.focus = elt
                elt.attributes["value"] = ""
                return self.render()
            elif elt.tag == "button":
                # elt is the button we clicked
                while elt:
                    if elt.tag == "form" and "action" in elt.attributes:
                        self.submit_form(elt)
                    elt = elt.parent
            if elt is not None:
                elt = elt.parent

    # elt is the node of the <form> tag
    def submit_form(self, elt):
        # find all <input> tags that are descendents of elt
        inputs = [node for node in tree_to_list(elt, [])
                  if isinstance(node, Element)
                  and node.tag == "input"
                  and "name" in node.attributes]
        # form encode the key-value pairs
        body = ""
        for input in inputs:
            name = input.attributes["name"]
            value = input.attributes.get("value", "")
            name = urllib.parse.quote(name)
            value = urllib.parse.quote(value)
            body += "&" + name + "=" + value
        body = body[1:]

        url = elt.attributes["action"]
        url = resolve_url(url, self.url)

        self.load(url, body)

    def scrolldown(self):
        max_y = max(self.document.height - (HEIGHT - CHROME_PX), 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)

    def scrollup(self):
        self.scroll = max(self.scroll - SCROLL_STEP, 0)

    def keypress(self, char):
        if self.focus:
            self.focus.attributes["value"] += char
            self.render()

    def draw(self, canvas):
        for cmd in self.display_list:
            if cmd.top > self.scroll + HEIGHT - CHROME_PX:
                continue
            if cmd.bottom < self.scroll:
                continue
            cmd.execute(self.scroll - CHROME_PX, canvas)

        if self.focus:
            obj = [obj for obj in tree_to_list(self.document, [])
                   if obj.node is self.focus][0]
            text = self.focus.attributes.get("value", "")
            x = obj.x + obj.font.measure(text)
            y = obj.y - self.scroll + CHROME_PX
            canvas.create_line(x, y, x, y + obj.height)

    def load(self, url, body=None):
        self.url = url
        self.scroll = 0
        self.focus = None
        self.history.append(url)
        headers, body = request(url, body)

        with open('test.html', 'r', encoding='utf-8') as f:
            body = f.read()

        self.nodes = HTMLParser(body).parse()
        print_tree(self.nodes)
        self.rules = self.default_style_sheet.copy()

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
            self.rules.extend(CSSParser(body).file())

        self.render()

    def render(self) -> None:
        # 원랜 load 말미에 있던 거
        style(self.nodes, sorted(self.rules, key=cascade_priority))
        self.document = DocumentLayout(self.nodes)
        self.document.layout()
        print_tree(self.document)

        self.display_list: List[DrawCmd] = []
        self.document.paint(self.display_list)

    def go_back(self) -> None:
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back)


CHROME_PX = 100


class Browser:
    def __init__(self) -> None:
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT, bg="white")
        self.canvas.pack()

        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)
        self.window.bind("<Button-1>", self.handle_click)
        self.window.bind("<Key>", self.handle_key)

        self.tabs: List[Tab] = []
        self.active_tab: Optional[int] = None

        self.focus: Optional[Union[Literal["address bar"], Literal["content"]]] = None

    def handle_key(self, e):
        if self.focus == "content":
            assert self.active_tab is not None
            self.tabs[self.active_tab].keypress(e.char)
            self.draw()

    def handle_down(self, event) -> None:
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrolldown()
        self.draw()

    def handle_up(self, event) -> None:
        assert self.active_tab is not None
        self.tabs[self.active_tab].scrollup()
        self.draw()

    def handle_click(self, event) -> None:
        if event.y < CHROME_PX:
            self.focus = None
            if 40 <= event.x < 40 + 80 * len(self.tabs) and 0 <= event.y < 40:
                self.active_tab = int((event.x - 40) / 80)
            elif 10 <= event.x < 30 and 10 <= event.y < 30:
                self.load("https://browser.engineering/")
            elif 10 <= event.x < 35 and 40 <= event.y < 90:
                assert self.active_tab is not None
                self.tabs[self.active_tab].go_back()
        else:
            self.focus = "content"
            assert self.active_tab is not None
            self.tabs[self.active_tab].click(event.x, event.y - CHROME_PX)
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        assert self.active_tab is not None
        self.tabs[self.active_tab].draw(self.canvas)
        self.canvas.create_rectangle(0, 0, WIDTH, CHROME_PX, fill="white", outline="black")

        tabfont = tkinter.font.Font(family="Times", size=20, weight="normal", slant="roman")  # you should call get_font instead

        for i, tab in enumerate(self.tabs):
            name = "Tab {}".format(i)
            x1, x2 = 40 + 80 * i, 120 + 80 * i

            self.canvas.create_line(x1, 0, x1, 40, fill="black")
            self.canvas.create_line(x2, 0, x2, 40, fill="black")
            self.canvas.create_text(x1 + 10, 10, anchor="nw", text=name,
                                    font=tabfont, fill="black")
            if i == self.active_tab:
                self.canvas.create_line(0, 40, x1, 40, fill="black")
                self.canvas.create_line(x2, 40, WIDTH, 40, fill="black")

        # new tab button
        buttonfont = tkinter.font.Font(family="Times", size=30, weight="normal", slant="roman")  # you should call get_font instead
        self.canvas.create_rectangle(10, 10, 30, 30, outline="black", width=1)
        self.canvas.create_text(11, 0, anchor="nw", text="+", font=buttonfont, fill="black")

        # address bar
        self.canvas.create_rectangle(40, 50, WIDTH - 10, 90, outline="black", width=1)
        url = self.tabs[self.active_tab].url
        self.canvas.create_text(55, 55, anchor='nw', text=url, font=buttonfont, fill="black")

        # back button
        self.canvas.create_rectangle(10, 50, 35, 90, outline="black", width=1)
        self.canvas.create_polygon(15, 70, 30, 55, 30, 85, fill='black')

    def load(self, url):
        new_tab = Tab()
        new_tab.load(url)
        self.active_tab = len(self.tabs)
        self.tabs.append(new_tab)
        self.draw()


# if payload == None, then send a GET request
# otherwise, send a POST request with the payload as the body
def request(url, payload=None):
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

    method = "POST" if payload is not None else "GET"

    body = (f"{method} {path} HTTP/1.0\r\n" +
            f"Host: {host}\r\n")

    if payload is not None:
        length = len(payload.encode("utf8"))
        body += f"Content-Length: {length}\r\n"

    body += "\r\n" + (payload or "")

    s.send(body.encode("utf8"))

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


@dataclasses.dataclass
class Text:
    text: str
    parent: Optional['Element'] = None
    children: List['Node'] = field(default_factory=list)

    def __repr__(self) -> str:
        return repr(self.text)


@dataclasses.dataclass
class Element:
    # Note: testing framework will try initialize elem = Element(tag, attr, parent) in this order
    tag: str
    attributes: Dict[str, str]
    # testing framework's order:
    parent: Optional['Element'] = None
    children: List['Node'] = field(default_factory=list)
    # original order as of May 4th:
    #
    # children: List['Node'] = field(default_factory=list)
    # parent: Optional['Element'] = None

    def __repr__(self) -> str:
        return "<" + str(self.tag) + ">"


# a Node is either Text or Element
Node = Union[Text, Element]


def print_tree(node, indent: int = 0):
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


INHERITED_PROPERTIES = {
    "font-size": "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black",
}


def compute_style(node, prop, val):
    if prop == "font-size":
        if val.endswith("px"):
            return val
        elif val.endswith("%"):
            if node.parent:
                parent_font_size = node.parent.style["font-size"]
            else:
                parent_font_size = INHERITED_PROPERTIES["font-size"]
            node_pct = float(val[:-1]) / 100
            parent_px = float(parent_font_size[:-2])
            return str(node_pct * parent_px) + "px"
        else:
            return None
    else:
        return val


def style(node, rules):
    node.style = {}

    for prop, default in INHERITED_PROPERTIES.items():
        if node.parent is not None:
            node.style[prop] = node.parent.style[prop]
        else:
            node.style[prop] = default

    for selector, body in rules:
        if selector.matches(node):
            for prop, val in body.items():
                computed_val = compute_style(node, prop, val)
                if not computed_val:
                    continue
                node.style[prop] = computed_val

    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for prop, val in pairs.items():
            computed_val = compute_style(node, prop, val)
            if not computed_val:
                continue
            node.style[prop] = computed_val

    for child in node.children:
        style(child, rules)


class TagSelector:
    def __init__(self, tag):
        self.tag = tag
        self.priority = 1

    def matches(self, node):
        return isinstance(node, Element) and node.tag == self.tag


class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority

    def matches(self, node):
        if not self.descendant.matches(node):
            return False
        while node.parent is not None:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False


def cascade_priority(rule):
    selector, body = rule
    return selector.priority


class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0  # index of the current character

    def literal(self, char):
        # fail unless the current character is char
        # otherwise, advance past the current character and do nothing else
        assert self.i < len(self.s) and self.s[self.i] == char, (self.s, self.i)
        self.i += 1

    # skip past all whitespace starting at self.i
    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    # parse a sequence of word-like characters
    # return the sequence of characters as a string
    def word(self):
        start = self.i
        while self.i < len(self.s) and (self.s[self.i].isalnum() or self.s[self.i] in "#-.%"):
            self.i += 1
        assert self.i > start
        return self.s[start:self.i]

    # parse and return a property-value pair
    # example:
    #    background-color: red;
    def pair(self):
        prop = self.word()
        self.whitespace()
        self.literal(':')
        self.whitespace()
        val = self.word()

        return (prop.lower(), val)

    def body(self):
        pairs = {}
        while self.i < len(self.s):
            try:
                (prop, val) = self.pair()
                pairs[prop] = val
                self.whitespace()
                self.literal(';')

                self.whitespace()
            except AssertionError:
                why = self.ignore_until(';}')
                if why == ';':
                    self.literal(';')
                    self.whitespace()
                else:
                    break

        return pairs

    # parses a space-separated sequence of words
    # builds a nested descendant selector tree to match those nodes
    def selector(self):
        first_tag = self.word().lower()
        result = TagSelector(first_tag)
        self.whitespace()

        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word().lower()
            result = DescendantSelector(result, TagSelector(tag))
            self.whitespace()

        return result

    def rule(self):
        self.whitespace()
        selector = self.selector()
        self.literal("{")
        self.whitespace()
        propvals = self.body()
        self.literal("}")
        return (selector, propvals)

    # the book calls this parse()
    def file(self):
        rules = []

        while self.i < len(self.s):
            try:
                rules.append(self.rule())
            except AssertionError:
                why = self.ignore_until("}")
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break

        return rules

    # skip characters until we see a character in chars
    def ignore_until(self, chars):
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            self.i += 1
        # return None


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

    def __repr__(self):
        return f"BlockLayout({self.node})"

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

    def __repr__(self):
        return "DocumentLayout"


class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []  # a list of TextLayout objects

    def __repr__(self) -> str:
        return "LineLayout ..."

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        if not self.children:
            self.height = 0
            return

        for child in self.children:
            child.layout()

        metrics = [child.font.metrics() for child in self.children]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max([metric["descent"] for metric in metrics])
        self.height = 1.25 * (max_ascent + max_descent)

    def paint(self, display_list):
        for child in self.children:
            child.paint(display_list)


# represents one word in a line
class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.children = []
        self.parent = parent
        self.previous = previous
        self.y: float

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)

        self.font = tkinter.font.Font(
                family="Times",
                size=size,
                weight=weight,
                slant=style,
            )

        self.width = self.font.measure(self.word)

        if self.previous:
            # add a space
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + self.previous.width + space
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self, display_list):
        color = self.node.style["color"]
        display_list.append(DrawText(
            self.x,
            self.y,
            self.word,
            self.font,
            color))

    def __repr__(self) -> str:
        return f"TextLayout({self.word}, {self.x=}, {self.y=}, {self.width=}, {self.height=})"


class InlineLayout:
    # An InlineLayout object has children which are LineLayout objects
    # (and the children of LineLayout are TextLayout objects)
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def __repr__(self):
        return f"InlineLayout({repr(self.node)})"

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x
        if self.previous is None:
            self.y = self.parent.y
        else:
            self.y = self.previous.y + self.previous.height

        self.cursor_x = self.x
        self.new_line()
        self.recurse(self.node)
        # at this point, the layout tree is constructed
        # but the layout computation not done yet
        for child in self.children:
            child.layout()
        self.height = sum(child.height for child in self.children)

    def text(self, node):
        # color = node.style["color"]

        for word in node.text.split():
            weight = node.style["font-weight"]
            style = node.style["font-style"]
            if style == "normal":
                style = "roman"
            size = int(float(node.style["font-size"][:-2]) * .75)

            font = tkinter.font.Font(
                    family="Times",
                    size=size,
                    weight=weight,
                    slant=style,
                )
            w = font.measure(word)

            if self.cursor_x + w >= self.width - HSTEP:
                self.new_line()

            line = self.children[-1]
            text = TextLayout(node, word, line, self.previous_word)
            line.children.append(text)
            self.previous_word = text
            # self.line.append((self.cursor_x, word, font, color))
            self.cursor_x += w + font.measure(" ")

    def new_line(self):
        self.previous_word = None
        self.cursor_x = self.x
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)

    def input(self, node) -> None:
        w = INPUT_WIDTH_PX
        if self.cursor_x + w > self.x + self.width:
            self.new_line()
        line = self.children[-1]
        input = InputLayout(node, line, self.previous_word)
        line.children.append(input)
        self.previous_word = input

        # you should call font = get_font(self.node) instead of all this
        # ### begin get_font stuff
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(node.style["font-size"][:-2]) * .75)

        font = tkinter.font.Font(
                family="Times",
                size=size,
                weight=weight,
                slant=style,
            )
        # ### end get_font stuff
        node.font = font

        self.cursor_x += w + font.measure(" ")

    def recurse(self, node: Node) -> None:
        if isinstance(node, Text):
            self.text(node)
        else:
            if node.tag == "br":
                self.new_line()
            elif node.tag == "input" or node.tag == "button":
                self.input(node)
            else:
                for c in node.children:
                    self.recurse(c)

    # def recurse(self, node: Node) -> None:
    #     if isinstance(node, Text):
    #         self.text(node)
    #     else:
    #         self.open_tag(node.tag)
    #         for c in node.children:
    #             self.recurse(c)
    #         self.close_tag(node.tag)


    def paint(self, display_list):
        bgcolor = self.node.style.get("background-color", "transparent")

        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)

        for child in self.children:
            child.paint(display_list)
        # for x, y, word, font, color in self.display_list:
        #     display_list.append(DrawText(x, y, word, font, color))


INPUT_WIDTH_PX = 200

class InputLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.children = []
        self.parent = parent
        self.previous = previous
        self.y: float

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal":
            style = "roman"
        size = int(float(self.node.style["font-size"][:-2]) * .75)

        self.font = tkinter.font.Font(
                family="Times",
                size=size,
                weight=weight,
                slant=style,
            )

        self.width = INPUT_WIDTH_PX

        if self.previous:
            # add a space
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + self.previous.width + space
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")

    def paint(self, display_list):
        bgcolor = self.node.style.get("background-color",
                                      "transparent")
        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            display_list.append(rect)

        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            text = self.node.children[0].text

        color = self.node.style["color"]
        display_list.append(
            DrawText(self.x, self.y, text, self.font, color))

    def __repr__(self) -> str:
        return f"InputLayout({self.x=}, {self.y=}, {self.width=}, {self.height=})"


def main(url: str) -> None:
    Browser().load(url)
    tkinter.mainloop()


if __name__ == "__main__":
    # main(sys.argv[1])
    url = 'https://browser.engineering/styles.html'
    main(url)
