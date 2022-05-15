---
created: 2022-05-15 06:10
tag: 🧑🏻‍💻 공부
title: ch 4. Constructing a Document Tree 
category: IT
start_date: 2022-05-15
finish_date: 
status: 
---
[TOC]
# ch 4. Constructing a Document Tree 
https://browser.engineering/html.html

- HTML은 tree 구조.
- 이 챕터에선 HTML 파서를 만들고, 이전에 만든 layout 엔진이 HTML 파서를 이용하게끔 할 예정

## parser
- paring 규칙 엄청나게 많음.
![[html5 parsing.png]]
- 규칙 어긋난 케이스도 많음 > 에러 핸들링 필수
![[mis-nested tags.png]]
- header 에 content types는 parser 를 지정하는 역할
![[content types.png]]
- 링크 리소스 (src) 같은 경우, parser 더 진행하기 전에 download 부터 해야한다고.
![[linked resource.png]]

## A tree of nodes
- DOM tree 를 의미
	- Document Object Model
- 태그쌍(+content) 하나에 하나의 노드
	- tree 화를 위해 이전의 tokens을 노드로 전환할 필요.
- 아직 안 닫긴 태그는 늘 닫긴 태그 오른쪽에 위치, 
	To leverage these facts, let’s represent an incomplete tree by storing a list of unfinished tags, ordered with parents before children. The first node in the list is the root of the HTML tree; the last node in the list is the most recent unfinished tag.
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
- text 를 node화 시키기?

```python
def add_text(self, text):  
	# tag에서 !doctype 버리기로 해서 다음 줄에 바로 \n 나옴...크러쉬 남.  
	# 일단 공백은 무시하는 걸로... 
	if text.isspace(): return
    parent = self.unfinished[-1] # text의 부모는 바로 이전에 열려 있는 tag(Element)
    node = Text(text, parent)  
    parent.children.append(node)  # 각 parent 가 Text class.  
  
def add_tag(self, tag):  
	# 최초의 <!doctype html> 은 태그가 아님...일단 여기선 그냥 버리기로.
	if tag.startswith("!"): return  
    if tag.startswith("/"):  # close tag  
        if len(self.unfinished) == 1: return  # 마지막 태그  
        node = self.unfinished.pop()  # latest를 pop  
        parent = self.unfinished[-1]  
		# tag closed 된 것만 child가 될 수 있음.  
		# closed 되면 바로 앞의 unfinished 가 해당 node의 부모가 됨.
        parent.children.append(node)  
    else: # open tag  
		# 제일 처음과 마지막은 parent 없음.  
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

- 각 node가 Text 혹은 Element class 
	- parent, children을 가지고 있고, 계속 맞물려서 tree를 이어나감. 
	- ex) body 가 "`<!DOCTYPE html>\n`" 이렇게 시작하고, '\n'까지 Text node를 만든 경우
	```
		- self.unfinished : [<!DOCTYPE html>]
		- (Text) node : '\n'
		- node.parent : <!DOCTYPE html> 
		- node.parent.children : []
	```
	- ex) ``link rel ...> '\n\n ' <title>'asdf'</title> 일 때`
	```
		- node : <title>
		- node.childrent = ['asdf']
		- parent : <link rel~~~> 
		- parent.children = ['\n\n ']
		- add_tag 실행 후 > parent.children = ['\n\n ', '<title>']
	
	```


## Self-closing tags
- 클로징 태그가 따로 없는 것들이 있음.
![[attributes.png]]
```
SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]
```
- 보통 `<meta name="generator" content="pandoc" />` 이런 식으로 내부에 name, content 같은 attributes 들이 있음. attributes도 처리해야함. 
```python
def add_tag(self, tag):
	... 
	elif tag in SELF_CLOSING_TAGS:  # attribute 처리해야함.  
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
			# value 가 "" 혹은 ''에 감싸져 있는 경우 벗겨내기  
			if len(value) > 2 and value[0] in ["'", "\""]:  
				value = value[1:-1]
			attributes[key.lower()] = value
		else:  # value 가 누락된(omit) 경우도 있음. ex) <input disabled>  
			attributes[attrpair.lower()] = ""
    return tag, attributes
```
- Element 에 attributes 담고, 기존 tag에선 attributes 벗겨내기
```python
class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        # ...
		
		
def add_tag(self, tag):
    tag, attributes = self.get_attributes(tag)
```
- 바꾼 결과 이게
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
- 이렇게 됨
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
- Layout class : 토큰 단위 > 노드 단위로 변경
- git 확인하기 : recurse로 재귀
- tree와 node의 차이 확실히 짚고 넘어가야 함.


## html 포맷 error 처리
- 아래의 html 기본 템플릿 (boilerplate) 을 사람이 빼먹는 경우, 자동으로 채워줘야 함.
- 현대의 브라우저는 다들 하고 있는 거.
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
- add_text와 add_tag 부분에 추가하면 위의 기능 넣어줄 수 있음.
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
    # 기본 html 템플릿 - html, head, body 없으면 자동으로 넣어주기  
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
		# </html> 채워넣기  
		# </body>, </html> 은 finish() 에서 처리함.
		elif open_tags == ["html", "head"]\
				and tag not in ["/head"] + self.HEAD_TAGS:  
			self.add_tag("/head")  
		else:  
			break
```
- 이거 외에서 format이 잘못된 케이스 많지만, 여기선 여기까지만.

[[ch 5. Laying Out Pages]]