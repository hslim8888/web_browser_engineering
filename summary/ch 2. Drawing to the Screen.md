---
created: 2022-05-07 23:46
tag: 🧑🏻‍💻 공부
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
- 윈도우 동작 & display 영역은 OS 환경에서 처리하는 것.
- 컨텐츠를 'drawing'하는 건 프로그램 (브라우저) 영역
- 클릭 같은 이벤트 이후에 redraw 하는 건데, 당연히 os와 프로그램의 상호 반응이 빨라야 유저가 feel fluid 하게 느낌
	- 60Hz 즉, 1/60초(16ms) 안 쪽으로 브라우저가 그래픽 갱신하는 게 끝나야.
	- 16ms == animation frame budget of the application
	- 애니메이션 액션이 아니라 마우스 클릭 같은 분절 액션은 100ms 도 괜찮.
	
- 프로그램적으로 처리하기 위해 그래픽 툴킷 사용. 
- python : tkinter
```python
import tkinter
window = tkinter.Tk()
tkinter.mainloop()
```
아래와 같이 창이 생김 - 크롬창이 아니라 python 실행기?
![[tk_window.png]]

## Drawing to the window
![[canvas_widget.png]]

```python
WIDTH, HEIGHT = 800, 600
# 윈도우 생성
window = tkinter.Tk() 
# 윈도우 안에 캔버스 생성
canvas = tkinter.Canvas(window, width=WIDTH, height=HEIGHT) 
canvas.pack()
```

- **layout** 다음에 **rendering**
- 그래서 캔버스는 display list를 실행시키기 전에 커맨드 (여기선 layout을 의미??) 를 저장해놓는데, 
	1) 페이지가 바뀌지 않으면 재사용하기 위해서
	2) 스크롤할 때 layout 을 다시 할 필요 없으니까
- 아래 소스에는 layout이 따로 없음...? layout은 그래픽 툴킷이 알아서 하는 건가? 저장도 알아서? ... 는 아님.. 밑에 보면 나옴.

- 캔버스 안에 그리기
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
- 텍스트 그리기
- **lex** : text not tags contents of an HTML document

```python
HSTEP, VSTEP = 13, 18
cursor_x, cursor_y = HSTEP, VSTEP
for c in text:
    self.canvas.create_text(cursor_x, cursor_y, text=c)
    cursor_x += HSTEP
	# 가로 다 차면 내리기
	if cursor_x >= WIDTH - HSTEP:
		cursor_y += VSTEP  # \n
		cursor_x = HSTEP   # \r
```
- 13, 18은 워드 프로세서의 매직 넘버 같은 거라고.
- 타자기 시절, 줄바꿈은 두 가지 동작이 필요
	1) 줄바꿈 - y 축 변경
	2) carriage return - x 축 초기화. 
	- 현재는 carriage가 없음에도 그 전통(?) 지키고 있는 것. 
	- 그래서 위에도 '\r\n'
![[print_text_from_response1.png]]

- y 축이 캔버스 디폴트보다 넘어가면 출력 못 함. > 스크롤 필요

## Scrolling text
![[scrolling.png]]

![[browser_rendering.png]]

![[display_list.png]]
- 일반적으로 브라우저는 page 부터 layout (배치?)한 뒤에, screen coordinates(좌표) 에 따라 rendering 을 한다고.
- layout 은 포지셔닝, rendering 은 그리는 것.
- 위의 소스는 load() 에 layout, rendering 이 전부 있음. 분리해보자.

1) layout
```python
def layout(self, text):
	display_list = []
	HSTEP, VSTEP = 13, 18
	cursor_x, cursor_y = HSTEP, VSTEP
	for c in text:
		display_list.append((cursor_x, cursor_y, c))
		...  # x, y 변경
	return display_list
```
- 소스를 보면, layout은 그려야할 텍스트(혹은 이미지 등등)와 그에 해당하는 좌표를 미리 다 계산해서 가지고 있는 행위

2) rendering
```python
def draw(self):
	for x, y, c in self.display_list:
	  self.canvas.create_text(x, y, text=c)
```

- 이미 전체 layout - display_list 를 가지고 있음.
- self.canvas.create_text(x, y - self.scroll, text=c) 로 scroll 값, 즉 y 값만 바꾸면 display 위치 변경 가능.
- 사용자 입력을 받아 scroll 값 변경해보자!

## Reacting to the user
- 심플하게 하기 위해 down key만 구현
- Tk 라이브러리로 key binding function 구현 가능.
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
- scrolldown에서 layout은 재사용
- draw, 즉 rendering 만 다시 함.

- 실행하면 이전 렌더링에 덮어씀. draw 하기 전에 이전꺼 지워야 함. 
```python
def draw(self):
    self.canvas.delete("all")
```

... 오 잘 된다.

## Faster rendering
- 동작 잘 하는데, 느림.
- 스크린 밖의 문자까지 전부 draw 하고 있기 때문.
- 물론 그 밖에도 렌더링 최적화하는 방법 많지만 여기선 이것만.
```python
for x, y, c in self.display_list:
    if y > self.scroll + HEIGHT: continue
    if y + VSTEP < self.scroll: continue
    # ...
```

..으로도 엄청 빨라짐. 16ms animation frame budget 까지 되는지는 모르겠지만.


## Mobile devices
- 모바일은 비슷하지만 아래 사항들이 다름.
-   Applications are usually full-screen, with only one application drawing to the screen at a time. Also, “background” applications may be killed and restarted at any time.
-   There is always a touch screen, no mouse, and a virtual keyboard instead of a physical one.
-   There is a concept of a “visual viewport” not present on desktop. Look at the source of this webpage. In the `<head>` you’ll see a “viewport” `<meta>` tag. This tag gives instructions to the browser for how to handle zooming on a mobile device. Without this tag, the browser makes assumptions, for historical reasons, that the site is “desktop-only” and needs some special tricks to make it readable on a mobile device, such as allowing the user to use a pinch-zoom or double-tap touchscreen gesture to focus in on one part of the page. Once zoomed in, the part of the page visible on the screen is the “visual viewport” and the whole documents’ bounds are the “layout viewport”.
-   Screen pixel density is much higher, and the total screen resolution is lower.
-   Power efficiency is much more important, because the device runs on a battery, while at the same time the CPU and memory are significantly slower and less capable. As a a result, it becomes more important to take advantage of GPU hardware on these devices, as well as an even greater focus on performance than usual.

[[ch 3. Formatting Text]]