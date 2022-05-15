import dataclasses
import tkinter
import tkinter.font
import socket
import ssl
import sys


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)

    def scrolldown(self, event):
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollup(self, event):
        self.scroll -= SCROLL_STEP
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, word, font in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y < self.scroll - VSTEP:
                continue
            self.canvas.create_text(x, y - self.scroll, text=word, anchor="nw",
                                    font=font)

    def load(self, url):
        headers, body = request(url)
        self.nodes = HTMLParser(body).parse()
        self.display_list = Layout(self.nodes).display_list
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
    def __init__(self, text, parent):
        self.text = text
        self.children = []
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


@dataclasses.dataclass
class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent

    def __repr__(self):
        return "<" + self.tag + ">"


class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []

    def parse(self):
        text = ""
        inside_tag = False
        for c in self.body:
            if c == "<":
                inside_tag = True
                if text: self.add_text(text)
                text = ""
            elif c == ">":
                inside_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        if not inside_tag and text:
            self.add_text(text)
        return self.finish()

    def add_text(self, text):
        # tag에서 !doctype 버리기로 해서 다음 줄에 바로 \n 나옴...크러쉬 남.
        # 일단 공백은 무시하는 걸로...
        if text.isspace(): return
        parent = self.unfinished[-1] # 가장 마지막 unfinished 가 새로운 text의 부모
        node = Text(text, parent)
        parent.children.append(node)  # 각 parent 가 Text class.

    def add_tag(self, tag):
        # tag 에서 attributes 벗겨내기
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return  # <!doctype html> 은 태그가 아님...일단 여기선 그냥 버리기로.

        if tag.startswith("/"):  # close tag
            if len(self.unfinished) == 1: return  # 마지막 태그
            node = self.unfinished.pop()  # latest를 pop??
            parent = self.unfinished[-1]
            parent.children.append(node)  # tag closed 된 것만 child가 될 수 있음.

        elif tag in SELF_CLOSING_TAGS:  # attribute 처리해야함.
            parent = self.unfinished[-1]
            node = Element(tag, parent, attributes)
            parent.children.append(node)

        else: # open tag
            parent = self.unfinished[-1] if self.unfinished else None # 제일 처음과 마지막은 parent 없음.
            node = Element(tag, parent, attributes)
            self.unfinished.append(node)

    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].lower()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                # value 가 "" 혹은 ''에 감싸져 있는 경우 벗겨내기
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]
                attributes[key.lower()] = value
            else:  # value 가 누락된(omit) 경우도 있음. ex) <input disabled>
                attributes[attrpair.lower()] = ""
        return tag, attributes

    def finish(self):
        if len(self.unfinished) == 0:
            self.add_tag("html")
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()


def print_tree(node, indent=0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)


class Layout:
    def __init__(self, nodes):
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.line = []
        self.display_list = []

        # for tok in tokens:
        #     self.token(tok)
        for tree in nodes.children:
            self.recurse(tree)
        self.flush()

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

        self.cursor_x = HSTEP
        self.line = []
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

    def open_tag(self, tag):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP

    def recurse(self, tree):
        if isinstance(tree, Text):
            self.text(tree)
        else:
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)



url = "http://example.org:8080/index.html"

# https://www.zggdwx.com/xiyou/1.html

if __name__ == "__main__":
    Browser().load('https://browser.engineering/html.html')
    tkinter.mainloop()
    # Browser().load(sys.argv[1])
    # tkinter.mainloop()
    # headers, body = request('https://browser.engineering/html.html')
    # nodes = HTMLParser(body).parse()
    # print_tree(nodes)
