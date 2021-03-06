---
created: 2022-05-08 08:23
tag: ๐ง๐ปโ๐ป ๊ณต๋ถ
title: ch 3. Formatting Text 
category: IT
start_date: 2022-05-08
finish_date: 
status: 
---
[TOC]
# ch 3. Formatting Text 
https://browser.engineering/text.html

## What is a font?
- ch2 ์์  ํ์๋ฅผ ๋ฟ๋ฆผ. ์์ด๋ ๊ฐ๋ก, ์ธ๋ก๊ฐ ๋ค๋ฆ. ๊ฐ์ ๋ฌธ์๋ผ๋ ํฐํธ๊ฐ ๋ค๋ฅด๋ฉด? 
- ch2 ์์  HSTEP, VSTEP์ด ๊ณ ์ ๊ฐ์ด๋ผ 13, 18๋ณด๋ค ํฐ ํฐํธ๋ก ๋ฐ๋๋ฉด ๋ฌธ์๋ผ๋ฆฌ ๊ฒน์น  ์๋ ์์.
 
### ํฐํธ์ ๊ด๋ จ๋ ์ฉ์ด
- ํฐํธ์ ์ด์ : ๊ธ์(๋ฉํ)๋ฅผ ๋ด์ case(uppercase, lowercase)๋ค์ ์ธํธ.
- type : a collection of fonts
- nomenclature : ๋ช๋ช๋ฒ
- Tk ๋ผ์ด๋ธ๋ฌ๋ฆฌ์ ํฐํธ๋ ์๋  ๋ฐฉ์์ ๋ช์นญ์ ์ฐ๊ณ  ์์.

```python
import tkinter.font

class Browser:
    def __init__(self):
        # ...
        bi_times = tkinter.font.Font(
            family="Times",
            size=16,
            weight="bold",
            slant="italic",
        )
canvas.create_text(200, 100, text="Hi!", font=bi_times)
```


## Measuring text
![[understanding fonts.png]]
![[dissecting a character.png]]

### ํฐํธ ์ฌ์ด์ฆ ๊ด๋ จ ์ฉ์ด
- ascent ๋ ๊ผญ๋๊ธฐ - baseline ๊ธฐ์ค
- descent ๋ ๋ฐ๋ฅ
- glyph : ์์ด ์ฌ์ ์์  ์ํ๋ฌธ์๋ฅผ ์๋ฏธ. 
	- ๋ฌดํผ ํญ์ glyph dependent

### ํ์คํธ ์ธก์  
```
>>> bi_times.metrics()
{'ascent': 15, 'descent': 7, 'linespace': 22, 'fixed': 0}
>>> bi_times.measure("Hi!")
31
```
- ํ์คํธ ๋ ๋๋ง์ os์ ์์ญ. ์ปด๋ง๋ค ์์ ๊ฐ์ด ๋ค๋ฅผ ์ ์์.

#### metrics()
- linespace = ascent + descent = 22 pixels
- ์์์ size=16์ธ๋ฐ?? 
	- size=16 >> 16 points - inch์ ๊ด๋ จ, pixel์ด ์๋๋ผ.
	- 16 points ๋ metal block์ ์ฌ์ด์ฆ. ๋ฐ๋ผ์ ๊ธ์ ์์ฒด๋ณด๋จ ํฌ๋ค.
	- ํฐํธ๋ง๋ค ๊ฐ์ size๋ผ๋ ์ ์ฒด ๋์ด(linespace)๊ฐ ๋ค๋ฆ
```
>>> tkinter.font.Font(family="Courier", size=16).metrics()
{'fixed': 1, 'ascent': 13, 'descent': 4, 'linespace': 17}
>>> tkinter.font.Font(family="Times", size=16).metrics()
{'fixed': 0, 'ascent': 14, 'descent': 4, 'linespace': 18}
>>> tkinter.font.Font(family="Helvetica", size=16).metrics()
{'fixed': 0, 'ascent': 15, 'descent': 4, 'linespace': 19}
```

#### measure()
- measure๋ width ์ธก์ 
```
>>> bi_times.measure("Hi!")
31
>>> bi_times.measure("H")
17
>>> bi_times.measure("i")
6
>>> bi_times.measure("!")
8
>>> 17 + 8 + 6  # ๋ sum์ด ๋ฑ ๋จ์ด์ง๋ ๊ฑด ์๋๋ผ๊ณ ...๋ ์์์  ๋ฐ์ฌ๋ฆผ ๋๋ฌธ?
31
```

#### overlapping
```python
font1 = tkinter.font.Font(family="Times", size=16)
font2 = tkinter.font.Font(family="Times", size=16, slant='italic')
x, y = 200, 200
canvas.create_text(x, y, text="Hello, ", font=font1)
x += font1.measure("Hello, ")
canvas.create_text(x, y, text="world!", font=font2) # ์ด๊ฑด ๋๋๋ฐ
canvas.create_text(x, y, text="overlapping!", font=font2) # ์ด๊ฑด ์๋จ
```
![[hellow_world.png]]
![[overlapping.png]]
- create_text(x, y, text='ํ์คํธ')  ์ด ๋ถ๋ถ์ด 'ํ์คํธ'์ '์ผํฐ'์์ x, y๊ฐ ์์๋๊ธฐ ๋๋ฌธ
- anchor๋ฅผ ์ค์ ํด์ ์์์ ์ top-left๋ก ์ก์์ค์ผ ํจ. 
	- nw : northwest
```python
x, y = 200, 225
canvas.create_text(x, y, text="Hello, ", font=font1, anchor='nw')
x += font1.measure("Hello, ")
canvas.create_text(x, y, text="overlapping!", font=font2, anchor='nw')
```


## Word by word
- ํ์๋ ๋ชจ๋  ๊ธ์ width๊ฐ ๊ฐ์์ ํ ๊ธ์์ฉ ๋ฟ๋ฆฌ๋ ๊ฒ ๋ง์ง๋ง, ์์ด๋ ์๋๋ผ ๋จ์ด ๋จ์๋ก ์ฒดํฌํ๋ ๊ฒ ์ข๋ค๊ณ .
```python
for word in text.split():
	w = font.measure(word)
	if cursor_x + w > WIDTH - HSTEP:
		cursor_y += font.metrics("linespace") * 1.25 # ์ค๋ฐ๊ฟ ๊ฐ๊ฒฉ
		cursor_x = HSTEP
	self.display_list.append((cursor_x, cursor_y, word))
	cursor_x += w + font.measure(" ") # split์ผ๋ก ๊ณต๋ฐฑ ์์ ์ ์ถ๊ฐ.
```
- ์ค๋ฐ๊ฟ ๊ฐ๊ฒฉ์ ๋ณดํต 25%

## Styling text
- `<b>` ํ๊ทธ ๋ `<i>` ๊ฐ์ ๊ฑธ๋ก ์คํ์ผ์ด ๋ง ๋ฐ๋๋ฉด?
-  ํ๊ทธ ์์ ์๋ ๊ฑด ๋ฐ๋ก Tag object์ ๋ด๊ณ , ์๋ ๊ฑด Text์ ๋ด์์ ์ฒ๋ฆฌํด์ผ
```python
def lex(body):
    out = []
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if text: out.append(Text(text))
            text = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
    if not in_tag and text:
        out.append(Text(text))
    return out
```

## Layout class ๋ฐ๋ก ๋นผ๊ธฐ
- ๋ฉ์น๊ฐ ์ปค์ ธ layout ์ ํด๋์ค๋ก ๋นผ์ผ ํจ.

## Text of different sizes
- `<small>a</small><big>A</big>` ๊ฐ์ ๊ฑฐ ํด๋ณด๋ฉด ๋ฌธ์ ๊ฐ
![[different_sizes.png]]
- baseline ์ด ์๋๋ผ top์ align์ด ๋ง์ถฐ์ ธ ์๋ค.
	- ์์ ํฐ ๊ฒ ์๊ณ , ์๋ ์์ ๊ฒ ์์ผ๋ฉด ๊ฒน์ณ์ง ์๋ ์์.
- ์ฆ, vertical position์ด horizental position ๊ณ์ฐ๋ ์ดํ์ ๊ณ์ฐ์ด ๋์ด์ผ ํ๋ค๋ ์๋ฏธ
- x, y ๊ณ์ฐ์ ๋๋ ์ผ ํจ.

### cal X
- x๋ฅผ ๊ณ์ฐํ๋ ๋ชฉ์ ์ ๋ผ์ธ์ ๋๋๊ธฐ ์ํจ.
- ๊ฐ ๋ผ์ธ์ x, word, font๋ฅผ ๋ด๊ณ 

### cal Y
- y ์์ฒด๋ ๊ฐ ๊ธ์์ top. ๊ทธ๋์ baseline ๊ธฐ์ค์ผ๋ก ๊ฐ ๊ธ์์ y๋ฅผ ๊ตฌํ๊ณ  y์์ ๊ธ์ ๊ทธ๋ฆผ.
- ๊ฐ ๋ผ์ธ์์ y ๊ฐ ๊ฐ์ฅ ํฐ ๊ฒ, max ascent๋ฅผ ๊ตฌํด์ผ ํจ.
```python
def flush(self):  
	if not self.line: return  
    metrics = [font.metrics() for x, word, font in self.line]  
	# max ascent ๋ฅผ ์์์ผ baseline ๊ทธ๋ฆด ์๊ฐ ์์.
    max_ascent = max([metric["ascent"] for metric in metrics])  
    baseline = self.cursor_y + 1.25 * max_ascent  
  
    for x, word, font in self.line:   
		# ๊ฐ ๊ธ์์ y ๋ baseline์์ ๊ฐ ๊ธ์์ ascent ๋งํผ ๋์ ๊ฒ(๋บ ๊ฒ)
        y = baseline - font.metrics('ascent')    
        self.display_list.append((x, y, word, font))  
    self.cursor_x = HSTEP  
    self.line = []  
  
    # max descent๋ ๊ณ์ฐํด์ ๋ค์ cursor_y๋ ๊ทธ๊ฒ๋ณด๋ค ๋ฐ์ผ๋ก ๊ฐ๊ฒ  
    max_descent = max([metric["descent"] for metric in metrics])  
    # ์๋ก์ด y๋ ๊ธฐ์กด baseline ์์ ๊ธฐ์กด max descent ๋ณด๋ค ๋ ๋ฐ์ผ๋ก ์์ผ ํจ.
    self.cursor_y = baseline + 1.25 * max_descent  
```


## Faster text layout
- ๋ชจ๋  ๊ธ์๋ณ๋ก ์คํ์ผ๋ง layout / ํฐํธ ์ธํ ์ ํ๊ธฐ ๋๋ฌธ์ ๋๋ฆผ.
- 'the' ๊ฐ์ด ๋ง์ด ์ฐ์ด๋ ๊ฑด ์บ์ฑํด์ ์๋ ๋์ผ ์ ์์.
- ํฐํธ ์ธํ์ ํ์ํ  ๋๋ง ํ๋ ์์ผ๋ก ๋ณ๊ฒฝํ๋ฉด, ์บ์ฑ ์ฌ์ฉ ๊ฐ๋ฅ. 

```
def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight, slant=slant)
        FONTS[key] = font
    return FONTS[key]
	
class Layout:
	def text(self, tok):
		font = get_font(self.size, self.weight, self.style)
		# ...
```

[[ch 4. Constructing a Document Tree]]