---
created: 2022-05-15 06:10
tag: ๐ง๐ปโ๐ป ๊ณต๋ถ
title: ch 4. Constructing a Document Tree 
category: IT
start_date: 2022-05-15
finish_date: 
status: 
---
[TOC]
# ch 4. Constructing a Document Tree 
https://browser.engineering/html.html

- HTML์ tree ๊ตฌ์กฐ.
- ์ด ์ฑํฐ์์  HTML ํ์๋ฅผ ๋ง๋ค๊ณ , ์ด์ ์ ๋ง๋  layout ์์ง์ด HTML ํ์๋ฅผ ์ด์ฉํ๊ฒ๋ ํ  ์์ 

## parser
- paring ๊ท์น ์์ฒญ๋๊ฒ ๋ง์.
![[html5 parsing.png]]
- ๊ท์น ์ด๊ธ๋ ์ผ์ด์ค๋ ๋ง์ > ์๋ฌ ํธ๋ค๋ง ํ์
![[mis-nested tags.png]]
- header ์ content types๋ parser ๋ฅผ ์ง์ ํ๋ ์ญํ 
![[content types.png]]
- ๋งํฌ ๋ฆฌ์์ค (src) ๊ฐ์ ๊ฒฝ์ฐ, parser ๋ ์งํํ๊ธฐ ์ ์ download ๋ถํฐ ํด์ผํ๋ค๊ณ .
![[linked resource.png]]

## A tree of nodes
- DOM tree ๋ฅผ ์๋ฏธ
	- Document Object Model
- ํ๊ทธ์(+content) ํ๋์ ํ๋์ ๋ธ๋
	- tree ํ๋ฅผ ์ํด ์ด์ ์ tokens์ ๋ธ๋๋ก ์ ํํ  ํ์.
- ์์ง ์ ๋ซ๊ธด ํ๊ทธ๋ ๋ ๋ซ๊ธด ํ๊ทธ ์ค๋ฅธ์ชฝ์ ์์น, 
	To leverage these facts, letโs represent an incomplete tree by storing a list of unfinished tags, ordered with parents before children. The first node in the list is the root of the HTML tree; the last node in the list is the most recent unfinished tag.
- lex > HTMLParser
```python
class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
	
	def parse(self):
		text = ""  
		inside_tag = False  
		for c in body:  
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
```

## Constructin the tree
- text ๋ฅผ nodeํ ์ํค๊ธฐ?

```python
def add_text(self, text):  
	# tag์์ !doctype ๋ฒ๋ฆฌ๊ธฐ๋ก ํด์ ๋ค์ ์ค์ ๋ฐ๋ก \n ๋์ด...ํฌ๋ฌ์ฌ ๋จ.  
	# ์ผ๋จ ๊ณต๋ฐฑ์ ๋ฌด์ํ๋ ๊ฑธ๋ก... 
	if text.isspace(): return
    parent = self.unfinished[-1] # text์ ๋ถ๋ชจ๋ ๋ฐ๋ก ์ด์ ์ ์ด๋ ค ์๋ tag(Element)
    node = Text(text, parent)  
    parent.children.append(node)  # ๊ฐ parent ๊ฐ Text class.  
  
def add_tag(self, tag):  
	# ์ต์ด์ <!doctype html> ์ ํ๊ทธ๊ฐ ์๋...์ผ๋จ ์ฌ๊ธฐ์  ๊ทธ๋ฅ ๋ฒ๋ฆฌ๊ธฐ๋ก.
	if tag.startswith("!"): return  
    if tag.startswith("/"):  # close tag  
        if len(self.unfinished) == 1: return  # ๋ง์ง๋ง ํ๊ทธ  
        node = self.unfinished.pop()  # latest๋ฅผ pop  
        parent = self.unfinished[-1]  
		# tag closed ๋ ๊ฒ๋ง child๊ฐ ๋  ์ ์์.  
		# closed ๋๋ฉด ๋ฐ๋ก ์์ unfinished ๊ฐ ํด๋น node์ ๋ถ๋ชจ๊ฐ ๋จ.
        parent.children.append(node)  
    else: # open tag  
		# ์ ์ผ ์ฒ์๊ณผ ๋ง์ง๋ง์ parent ์์.  
        parent = self.unfinished[-1] if self.unfinished else None 
        node = Element(tag, parent)  
        self.unfinished.append(node)  
  
def finish(self):  
    if len(self.unfinished) == 0:  
        self.add_tag("html")  
    while len(self.unfinished) > 1:  
        node = self.unfinished.pop()  
        parent = self.unfinished[-1]  
        parent.children.append(node)  
    return self.unfinished.pop()
```

- ๊ฐ node๊ฐ Text ํน์ Element class 
	- parent, children์ ๊ฐ์ง๊ณ  ์๊ณ , ๊ณ์ ๋ง๋ฌผ๋ ค์ tree๋ฅผ ์ด์ด๋๊ฐ. 
	- ex) body ๊ฐ "`<!DOCTYPE html>\n`" ์ด๋ ๊ฒ ์์ํ๊ณ , '\n'๊น์ง Text node๋ฅผ ๋ง๋  ๊ฒฝ์ฐ
	```
		- self.unfinished : [<!DOCTYPE html>]
		- (Text) node : '\n'
		- node.parent : <!DOCTYPE html> 
		- node.parent.children : []
	```
	- ex) ``link rel ...> '\n\n ' <title>'asdf'</title> ์ผ ๋`
	```
		- node : <title>
		- node.childrent = ['asdf']
		- parent : <link rel~~~> 
		- parent.children = ['\n\n ']
		- add_tag ์คํ ํ > parent.children = ['\n\n ', '<title>']
	
	```


## Self-closing tags
- ํด๋ก์ง ํ๊ทธ๊ฐ ๋ฐ๋ก ์๋ ๊ฒ๋ค์ด ์์.
![[attributes.png]]
```
SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]
```
- ๋ณดํต `<meta name="generator" content="pandoc" />` ์ด๋ฐ ์์ผ๋ก ๋ด๋ถ์ name, content ๊ฐ์ attributes ๋ค์ด ์์. attributes๋ ์ฒ๋ฆฌํด์ผํจ. 
```python
def add_tag(self, tag):
	... 
	elif tag in SELF_CLOSING_TAGS:  # attribute ์ฒ๋ฆฌํด์ผํจ.  
		parent = self.unfinished[-1]  
		node = Element(tag, parent)  
		parent.children.append(node)

def get_attributes(self, text):  
    parts = text.split()  
    tag = parts[0].lower()  
    attributes = {}  
    for attrpair in parts[1:]:  
		if "=" in attrpair:  
			key, value = attrpair.split("=", 1)  
			# value ๊ฐ "" ํน์ ''์ ๊ฐ์ธ์ ธ ์๋ ๊ฒฝ์ฐ ๋ฒ๊ฒจ๋ด๊ธฐ  
			if len(value) > 2 and value[0] in ["'", "\""]:  
				value = value[1:-1]
			attributes[key.lower()] = value
		else:  # value ๊ฐ ๋๋ฝ๋(omit) ๊ฒฝ์ฐ๋ ์์. ex) <input disabled>  
			attributes[attrpair.lower()] = ""
    return tag, attributes
```
- Element ์ attributes ๋ด๊ณ , ๊ธฐ์กด tag์์  attributes ๋ฒ๊ฒจ๋ด๊ธฐ
```python
class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        # ...
		
		
def add_tag(self, tag):
    tag, attributes = self.get_attributes(tag)
```
- ๋ฐ๊พผ ๊ฒฐ๊ณผ ์ด๊ฒ
```
<html lang="en-US" xml:lang="en-US">
   <head>
     <meta charset="utf-8" />
       <meta name="generator" content="pandoc" />
         <meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=yes" />
           <meta name="author" content="Pavel Panchekha &amp; Chris Harrelson" />
             <link rel="stylesheet" href="book.css" />
               <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Vollkorn%7CLora&display=swap" />
                 <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Vollkorn:400i%7CLora:400i&display=swap" />
                   <title>
```
- ์ด๋ ๊ฒ ๋จ
```
<html>
   <head>
     <meta>
     <meta>
     <meta>
     <meta>
     <link>
     <link>
     <link>
     <title>
```

## Using the node tree
- Layout class : ํ ํฐ ๋จ์ > ๋ธ๋ ๋จ์๋ก ๋ณ๊ฒฝ
- git ํ์ธํ๊ธฐ : recurse๋ก ์ฌ๊ท
- tree์ node์ ์ฐจ์ด ํ์คํ ์ง๊ณ  ๋์ด๊ฐ์ผ ํจ.


## html ํฌ๋งท error ์ฒ๋ฆฌ
- ์๋์ html ๊ธฐ๋ณธ ํํ๋ฆฟ (boilerplate) ์ ์ฌ๋์ด ๋นผ๋จน๋ ๊ฒฝ์ฐ, ์๋์ผ๋ก ์ฑ์์ค์ผ ํจ.
- ํ๋์ ๋ธ๋ผ์ฐ์ ๋ ๋ค๋ค ํ๊ณ  ์๋ ๊ฑฐ.
![[html document.png]]
``
```
<!doctype html>
<html>
  <head>
  </head>
  <body>
  </body>
</html>
```
- add_text์ add_tag ๋ถ๋ถ์ ์ถ๊ฐํ๋ฉด ์์ ๊ธฐ๋ฅ ๋ฃ์ด์ค ์ ์์.
```python
class HTMLParser:
    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        # ...

    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"): return
        self.implicit_tags(tag)
        # ...


def implicit_tags(self, tag):  
    # ๊ธฐ๋ณธ html ํํ๋ฆฟ - html, head, body ์์ผ๋ฉด ์๋์ผ๋ก ๋ฃ์ด์ฃผ๊ธฐ  
    while True:  
		open_tags = [node.tag for node in self.unfinished]  
		if open_tags == [] and tag != "html":  
			self.add_tag("html")  
		elif open_tags == ["html"] \
				and tag not in ["head", "body", "/html"]:  
			if tag in self.HEAD_TAGS:  
				self.add_tag("head")  
			else:  
				self.add_tag("body")  
		# </html> ์ฑ์๋ฃ๊ธฐ  
		# </body>, </html> ์ finish() ์์ ์ฒ๋ฆฌํจ.
		elif open_tags == ["html", "head"]\
				and tag not in ["/head"] + self.HEAD_TAGS:  
			self.add_tag("/head")  
		else:  
			break
```
- ์ด๊ฑฐ ์ธ์์ format์ด ์๋ชป๋ ์ผ์ด์ค ๋ง์ง๋ง, ์ฌ๊ธฐ์  ์ฌ๊ธฐ๊น์ง๋ง.

[[ch 5. Laying Out Pages]]