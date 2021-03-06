---
created: 2022-05-07 23:46
tag: ๐ง๐ปโ๐ป ๊ณต๋ถ
title: ch 2. Drawing to the Screen 
category: IT
start_date: 2022-05-07
finish_date: 2022-05-08
status: 
---
[TOC]
# ch 2. Drawing to the Screen 
https://browser.engineering/graphics.html

## Creating Windows
- ์๋์ฐ ๋์ & display ์์ญ์ OS ํ๊ฒฝ์์ ์ฒ๋ฆฌํ๋ ๊ฒ.
- ์ปจํ์ธ ๋ฅผ 'drawing'ํ๋ ๊ฑด ํ๋ก๊ทธ๋จ (๋ธ๋ผ์ฐ์ ) ์์ญ
- ํด๋ฆญ ๊ฐ์ ์ด๋ฒคํธ ์ดํ์ redraw ํ๋ ๊ฑด๋ฐ, ๋น์ฐํ os์ ํ๋ก๊ทธ๋จ์ ์ํธ ๋ฐ์์ด ๋นจ๋ผ์ผ ์ ์ ๊ฐ feel fluid ํ๊ฒ ๋๋
	- 60Hz ์ฆ, 1/60์ด(16ms) ์ ์ชฝ์ผ๋ก ๋ธ๋ผ์ฐ์ ๊ฐ ๊ทธ๋ํฝ ๊ฐฑ์ ํ๋ ๊ฒ ๋๋์ผ.
	- 16ms == animation frame budget of the application
	- ์ ๋๋ฉ์ด์ ์ก์์ด ์๋๋ผ ๋ง์ฐ์ค ํด๋ฆญ ๊ฐ์ ๋ถ์  ์ก์์ 100ms ๋ ๊ด์ฐฎ.
	
- ํ๋ก๊ทธ๋จ์ ์ผ๋ก ์ฒ๋ฆฌํ๊ธฐ ์ํด ๊ทธ๋ํฝ ํดํท ์ฌ์ฉ. 
- python : tkinter
```python
import tkinter
window = tkinter.Tk()
tkinter.mainloop()
```
์๋์ ๊ฐ์ด ์ฐฝ์ด ์๊น - ํฌ๋กฌ์ฐฝ์ด ์๋๋ผ python ์คํ๊ธฐ?
![[tk_window.png]]

## Drawing to the window
![[canvas_widget.png]]

```python
WIDTH, HEIGHT = 800, 600
# ์๋์ฐ ์์ฑ
window = tkinter.Tk() 
# ์๋์ฐ ์์ ์บ๋ฒ์ค ์์ฑ
canvas = tkinter.Canvas(window, width=WIDTH, height=HEIGHT) 
canvas.pack()
```

- **layout** ๋ค์์ **rendering**
- ๊ทธ๋์ ์บ๋ฒ์ค๋ display list๋ฅผ ์คํ์ํค๊ธฐ ์ ์ ์ปค๋งจ๋ (์ฌ๊ธฐ์  layout์ ์๋ฏธ??) ๋ฅผ ์ ์ฅํด๋๋๋ฐ, 
	1) ํ์ด์ง๊ฐ ๋ฐ๋์ง ์์ผ๋ฉด ์ฌ์ฌ์ฉํ๊ธฐ ์ํด์
	2) ์คํฌ๋กคํ  ๋ layout ์ ๋ค์ ํ  ํ์ ์์ผ๋๊น
- ์๋ ์์ค์๋ layout์ด ๋ฐ๋ก ์์...? layout์ ๊ทธ๋ํฝ ํดํท์ด ์์์ ํ๋ ๊ฑด๊ฐ? ์ ์ฅ๋ ์์์? ... ๋ ์๋.. ๋ฐ์ ๋ณด๋ฉด ๋์ด.

- ์บ๋ฒ์ค ์์ ๊ทธ๋ฆฌ๊ธฐ
```python
class Browser:
	def __init__(self):
		self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
		
    def load(self):
        self.canvas.create_rectangle(10, 20, 400, 300)
        self.canvas.create_oval(100, 100, 150, 150)
        self.canvas.create_text(200, 150, text="Hi!")

if __name__ == "__main__":
    import sys
    Browser().load()
    tkinter.mainloop()
```
![[tk_result.png]]


## Laying out text
- ํ์คํธ ๊ทธ๋ฆฌ๊ธฐ
- **lex** : text not tags contents of an HTML document

```python
HSTEP, VSTEP = 13, 18
cursor_x, cursor_y = HSTEP, VSTEP
for c in text:
    self.canvas.create_text(cursor_x, cursor_y, text=c)
    cursor_x += HSTEP
	# ๊ฐ๋ก ๋ค ์ฐจ๋ฉด ๋ด๋ฆฌ๊ธฐ
	if cursor_x >= WIDTH - HSTEP:
		cursor_y += VSTEP  # \n
		cursor_x = HSTEP   # \r
```
- 13, 18์ ์๋ ํ๋ก์ธ์์ ๋งค์ง ๋๋ฒ ๊ฐ์ ๊ฑฐ๋ผ๊ณ .
- ํ์๊ธฐ ์์ , ์ค๋ฐ๊ฟ์ ๋ ๊ฐ์ง ๋์์ด ํ์
	1) ์ค๋ฐ๊ฟ - y ์ถ ๋ณ๊ฒฝ
	2) carriage return - x ์ถ ์ด๊ธฐํ. 
	- ํ์ฌ๋ carriage๊ฐ ์์์๋ ๊ทธ ์ ํต(?) ์งํค๊ณ  ์๋ ๊ฒ. 
	- ๊ทธ๋์ ์์๋ '\r\n'
![[print_text_from_response1.png]]

- y ์ถ์ด ์บ๋ฒ์ค ๋ํดํธ๋ณด๋ค ๋์ด๊ฐ๋ฉด ์ถ๋ ฅ ๋ชป ํจ. > ์คํฌ๋กค ํ์

## Scrolling text
![[scrolling.png]]

![[browser_rendering.png]]

![[display_list.png]]
- ์ผ๋ฐ์ ์ผ๋ก ๋ธ๋ผ์ฐ์ ๋ page ๋ถํฐ layout (๋ฐฐ์น?)ํ ๋ค์, screen coordinates(์ขํ) ์ ๋ฐ๋ผ rendering ์ ํ๋ค๊ณ .
- layout ์ ํฌ์ง์๋, rendering ์ ๊ทธ๋ฆฌ๋ ๊ฒ.
- ์์ ์์ค๋ load() ์ layout, rendering ์ด ์ ๋ถ ์์. ๋ถ๋ฆฌํด๋ณด์.

1) layout
```python
def layout(self, text):
	display_list = []
	HSTEP, VSTEP = 13, 18
	cursor_x, cursor_y = HSTEP, VSTEP
	for c in text:
		display_list.append((cursor_x, cursor_y, c))
		...  # x, y ๋ณ๊ฒฝ
	return display_list
```
- ์์ค๋ฅผ ๋ณด๋ฉด, layout์ ๊ทธ๋ ค์ผํ  ํ์คํธ(ํน์ ์ด๋ฏธ์ง ๋ฑ๋ฑ)์ ๊ทธ์ ํด๋นํ๋ ์ขํ๋ฅผ ๋ฏธ๋ฆฌ ๋ค ๊ณ์ฐํด์ ๊ฐ์ง๊ณ  ์๋ ํ์

2) rendering
```python
def draw(self):
	for x, y, c in self.display_list:
	  self.canvas.create_text(x, y, text=c)
```

- ์ด๋ฏธ ์ ์ฒด layout - display_list ๋ฅผ ๊ฐ์ง๊ณ  ์์.
- self.canvas.create_text(x, y - self.scroll, text=c) ๋ก scroll ๊ฐ, ์ฆ y ๊ฐ๋ง ๋ฐ๊พธ๋ฉด display ์์น ๋ณ๊ฒฝ ๊ฐ๋ฅ.
- ์ฌ์ฉ์ ์๋ ฅ์ ๋ฐ์ scroll ๊ฐ ๋ณ๊ฒฝํด๋ณด์!

## Reacting to the user
- ์ฌํํ๊ฒ ํ๊ธฐ ์ํด down key๋ง ๊ตฌํ
- Tk ๋ผ์ด๋ธ๋ฌ๋ฆฌ๋ก key binding function ๊ตฌํ ๊ฐ๋ฅ.
```python
SCROLL_STEP = 100
def __init__(self):
    # ...
    self.window.bind("<Down>", self.scrolldown)

def scrolldown(self, e):
	self.scroll += SCROLL_STEP
	self.draw()

def draw(self):
	for x, y, c in self.display_list:
		self.canvas.create_text(x, y - self.scroll, text=c)
```
- scrolldown์์ layout์ ์ฌ์ฌ์ฉ
- draw, ์ฆ rendering ๋ง ๋ค์ ํจ.

- ์คํํ๋ฉด ์ด์  ๋ ๋๋ง์ ๋ฎ์ด์. draw ํ๊ธฐ ์ ์ ์ด์ ๊บผ ์ง์์ผ ํจ. 
```python
def draw(self):
    self.canvas.delete("all")
```

... ์ค ์ ๋๋ค.

## Faster rendering
- ๋์ ์ ํ๋๋ฐ, ๋๋ฆผ.
- ์คํฌ๋ฆฐ ๋ฐ์ ๋ฌธ์๊น์ง ์ ๋ถ draw ํ๊ณ  ์๊ธฐ ๋๋ฌธ.
- ๋ฌผ๋ก  ๊ทธ ๋ฐ์๋ ๋ ๋๋ง ์ต์ ํํ๋ ๋ฐฉ๋ฒ ๋ง์ง๋ง ์ฌ๊ธฐ์  ์ด๊ฒ๋ง.
```python
for x, y, c in self.display_list:
    if y > self.scroll + HEIGHT: continue
    if y + VSTEP < self.scroll: continue
    # ...
```

..์ผ๋ก๋ ์์ฒญ ๋นจ๋ผ์ง. 16ms animation frame budget ๊น์ง ๋๋์ง๋ ๋ชจ๋ฅด๊ฒ ์ง๋ง.


## Mobile devices
- ๋ชจ๋ฐ์ผ์ ๋น์ทํ์ง๋ง ์๋ ์ฌํญ๋ค์ด ๋ค๋ฆ.
-   Applications are usually full-screen, with only one application drawing to the screen at a time. Also, โbackgroundโ applications may be killed and restarted at any time.
-   There is always a touch screen, no mouse, and a virtual keyboard instead of a physical one.
-   There is a concept of a โvisual viewportโ not present on desktop.ย Look at the source of this webpage. In theย `<head>`ย youโll see a โviewportโย `<meta>`ย tag. This tag gives instructions to the browser for how to handle zooming on a mobile device. Without this tag, the browser makes assumptions, for historical reasons, that the site is โdesktop-onlyโ and needs some special tricks to make it readable on a mobile device, such as allowing the user to use a pinch-zoom or double-tap touchscreen gesture to focus in on one part of the page. Once zoomed in, the part of the page visible on the screen is the โvisual viewportโ and the whole documentsโ bounds are the โlayout viewportโ.
-   Screen pixel density is much higher, and the total screen resolution is lower.
-   Power efficiency is much more important, because the device runs on a battery, while at the same time the CPU and memory are significantly slower and less capable. As a a result, it becomes more important to take advantage of GPU hardware on these devices, as well as an even greater focus on performance than usual.

[[ch 3. Formatting Text]]