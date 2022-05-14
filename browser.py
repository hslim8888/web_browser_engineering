import dataclasses
import tkinter
import tkinter.font
import socket
import ssl
import sys


WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100


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
        # show(body)
        self.canvas.create_rectangle(10, 20, 400, 300)
        self.canvas.create_oval(100, 100, 150, 150)
        self.canvas.create_text(200, 150, text="Hi!")

        tokens = lex(body)
        self.display_list = Layout(tokens).display_list
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


@dataclasses.dataclass
class Tag:
    tag: str


# lex("<b>Hello</b> <i>world!</i>")
# desired output: [Tag("b"), Text("Hello"), Tag("/b"), Text(" "),
#                  Tag("i"), Text("world!"), Tag("/i")]

def lex(body):  # return a list of tokens
    tokens = []
    text = ""
    inside_tag = False
    for c in body:
        if c == "<":
            inside_tag = True
            if text != "":
                tokens.append(Text(text))
            text = ""
        elif c == ">":
            inside_tag = False
            tokens.append(Tag(text))
            text = ""
        else:
            text += c
    if not inside_tag and text != "":
        tokens.append(Text(text))

    return tokens


class Layout:
    def __init__(self, tokens):
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16
        self.line = []
        self.display_list = []

        for tok in tokens:
            self.token(tok)
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

    def token(self, tok):
        if isinstance(tok, Text):
            self.text(tok)
        else:
            assert isinstance(tok, Tag)
            if tok.tag == "i":
                self.style = "italic"
            elif tok.tag == "/i":
                self.style = "roman"
            elif tok.tag == "b":
                self.weight = "bold"
            elif tok.tag == "/b":
                self.weight = "normal"
            elif tok.tag == "small":
                self.size -= 2
            elif tok.tag == "/small":
                self.size += 2
            elif tok.tag == "big":
                self.size += 4
            elif tok.tag == "/big":
                self.size -= 4
            elif tok.tag == "br":
                self.flush()
            elif tok.tag == "/p":
                self.flush()
                self.cursor_y += VSTEP



url = "http://example.org:8080/index.html"

# https://www.zggdwx.com/xiyou/1.html

if __name__ == "__main__":
    Browser().load(sys.argv[1])
    tkinter.mainloop()
