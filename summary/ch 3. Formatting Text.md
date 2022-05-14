---
created: 2022-05-08 08:23
tag: 🧑🏻‍💻 공부
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
- ch2 에선 한자를 뿌림. 영어는 가로, 세로가 다름. 같은 문자라도 폰트가 다르면? 
- ch2 에선 HSTEP, VSTEP이 고정값이라 13, 18보다 큰 폰트로 바뀌면 문자끼리 겹칠 수도 있음.
 
### 폰트와 관련된 용어
- 폰트의 어원 : 글자(메탈)를 담은 case(uppercase, lowercase)들의 세트.
- type : a collection of fonts
- nomenclature : 명명법
- Tk 라이브러리의 폰트도 옛날 방식의 명칭을 쓰고 있음.

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

### 폰트 사이즈 관련 용어
- ascent 는 꼭대기 - baseline 기준
- descent 는 바닥
- glyph : 영어 사전에선 상형문자를 의미. 
	- 무튼 폭은 glyph dependent

### 텍스트 측정 
```
>>> bi_times.metrics()
{'ascent': 15, 'descent': 7, 'linespace': 22, 'fixed': 0}
>>> bi_times.measure("Hi!")
31
```
- 텍스트 렌더링은 os의 영역. 컴마다 위의 값이 다를 수 있음.

#### metrics()
- linespace = ascent + descent = 22 pixels
- 위에서 size=16인데?? 
	- size=16 >> 16 points - inch와 관련, pixel이 아니라.
	- 16 points 는 metal block의 사이즈. 따라서 글자 자체보단 크다.
	- 폰트마다 같은 size라도 전체 높이(linespace)가 다름
```
>>> tkinter.font.Font(family="Courier", size=16).metrics()
{'fixed': 1, 'ascent': 13, 'descent': 4, 'linespace': 17}
>>> tkinter.font.Font(family="Times", size=16).metrics()
{'fixed': 0, 'ascent': 14, 'descent': 4, 'linespace': 18}
>>> tkinter.font.Font(family="Helvetica", size=16).metrics()
{'fixed': 0, 'ascent': 15, 'descent': 4, 'linespace': 19}
```

#### measure()
- measure는 width 측정
```
>>> bi_times.measure("Hi!")
31
>>> bi_times.measure("H")
17
>>> bi_times.measure("i")
6
>>> bi_times.measure("!")
8
>>> 17 + 8 + 6  # 늘 sum이 딱 떨어지는 건 아니라고...는 소수점 반올림 때문?
31
```

#### overlapping
```python
font1 = tkinter.font.Font(family="Times", size=16)
font2 = tkinter.font.Font(family="Times", size=16, slant='italic')
x, y = 200, 200
canvas.create_text(x, y, text="Hello, ", font=font1)
x += font1.measure("Hello, ")
canvas.create_text(x, y, text="world!", font=font2) # 이건 되는데
canvas.create_text(x, y, text="overlapping!", font=font2) # 이건 안됨
```
![[hellow_world.png]]
![[overlapping.png]]
- create_text(x, y, text='텍스트')  이 부분이 '텍스트'의 '센터'에서 x, y가 시작되기 때문
- anchor를 설정해서 시작점을 top-left로 잡아줘야 함. 
	- nw : northwest
```python
x, y = 200, 225
canvas.create_text(x, y, text="Hello, ", font=font1, anchor='nw')
x += font1.measure("Hello, ")
canvas.create_text(x, y, text="overlapping!", font=font2, anchor='nw')
```


## Word by word
- 한자는 모든 글자 width가 같아서 한 글자씩 뿌리는 게 맞지만, 영어는 아니라 단어 단위로 체크하는 게 좋다고.
```python
for word in text.split():
	w = font.measure(word)
	if cursor_x + w > WIDTH - HSTEP:
		cursor_y += font.metrics("linespace") * 1.25 # 줄바꿈 간격
		cursor_x = HSTEP
	self.display_list.append((cursor_x, cursor_y, word))
	cursor_x += w + font.measure(" ") # split으로 공백 없애서 추가.
```
- 줄바꿈 간격은 보통 25%

## Styling text
- `<b>` 태그 나 `<i>` 같은 걸로 스타일이 막 바뀌면?
-  태그 안에 있는 건 따로 Tag object에 담고, 아닌 건 Text에 담아서 처리해야
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

## Layout class 따로 빼기
- 덩치가 커져 layout 은 클래스로 빼야 함.

## Text of different sizes
- `<small>a</small><big>A</big>` 같은 거 해보면 문제가
![[different_sizes.png]]
- baseline 이 아니라 top에 align이 맞춰져 있다.
	- 위에 큰 게 있고, 아래 작은 게 있으면 겹쳐질 수도 있음.
- 즉, vertical position이 horizental position 계산된 이후에 계산이 되어야 한다는 의미
- x, y 계산을 나눠야 함.

### cal X
- x를 계산하는 목적은 라인을 나누기 위함.
- 각 라인에 x, word, font를 담고

### cal Y
- y 자체는 각 글자의 top. 그래서 baseline 기준으로 각 글자의 y를 구하고 y에서 글자 그림.
- 각 라인에서 y 가 가장 큰 것, max ascent를 구해야 함.
```python
def flush(self):  
	if not self.line: return  
    metrics = [font.metrics() for x, word, font in self.line]  
	# max ascent 를 알아야 baseline 그릴 수가 있음.
    max_ascent = max([metric["ascent"] for metric in metrics])  
    baseline = self.cursor_y + 1.25 * max_ascent  
  
    for x, word, font in self.line:   
		# 각 글자의 y 는 baseline에서 각 글자의 ascent 만큼 높은 것(뺀 것)
        y = baseline - font.metrics('ascent')    
        self.display_list.append((x, y, word, font))  
    self.cursor_x = HSTEP  
    self.line = []  
  
    # max descent도 계산해서 다음 cursor_y는 그것보다 밑으로 가게  
    max_descent = max([metric["descent"] for metric in metrics])  
    # 새로운 y는 기존 baseline 에서 기존 max descent 보다 더 밑으로 와야 함.
    self.cursor_y = baseline + 1.25 * max_descent  
```


## Faster text layout
- 모든 글자별로 스타일링 layout / 폰트 세팅 을 하기 때문에 느림.
- 'the' 같이 많이 쓰이는 건 캐싱해서 속도 높일 수 있음.
- 폰트 세팅을 필요할 때만 하는 식으로 변경하면, 캐싱 사용 가능. 

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