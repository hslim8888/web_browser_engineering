---
created: 2022-05-07 01:25
tag:
- ๐ง๐ปโ๐ป ๊ณต๋ถ
- Web Browser Engineering
title: Downloading Web Pages
category: IT
start_date: 2020-05-07
finish_date: 2020-05-07
status: 
---
[TOC]
# Downloading Web Pages
https://browser.engineering/http.html

- ๋ธ๋ผ์ฐ์ ๋ฅผ ์ฐ๋ฉด ์ฒ์ ํ๋ ๊ฒ url์ ํตํด 1) ์ฐ๊ฒฐ, ์๋ฒ๋ก๋ถํฐ ์ ๋ณด๋ฅผ 2) ๋ค์ด๋ก๋

## 1) Connection to a server
- DNS > ip .. ๋ผ์ฐํฐ ๋ฑ๋ฑ์ ํตํด ์๋ฒ์ ์ฐ๊ฒฐ
![[urls.png]]
![[connecting to a host.png]]

## 2) Requesting information
![[http requests 1.png]]

### Method, Resource, Protocol(http) Version
- ์ฒซ ๋ฒ์งธ ๋ผ์ธ
- http version์ 0.9, 1.0, 1.1, 2.0 ์ด ์๋๋ฐ 1.1์ด ์คํ ๋ค๋, 2.0์ ๋ณต์กํ ์น ์ฑ๋ง ๊ฐ๋ฅ. ๋ธ๋ผ์ฐ์ ๋ ์ํํ๊ธฐ ํ๋  ๋ฏ?

### Headers
- header 
	- key: value ๋ก ๊ตฌ์ฑ
	- ๊ธฐ๋ณธ์ ์ผ๋ก Host, User-Agent ๋ฑ ์ด ์์. 

### Body
- Additional request content

## 3) Server's response
![[resposne.png]]
![[status code.png]]

response๋ request์ ๋ง์ฐฌ๊ฐ์ง๋ก 3 ํํธ๋ก ๊ตฌ์ฑ
### Protoco Version, Status Code, Explanation
### Headers
### Body

## <์ค์ต> Telent in Python
1. url ์์ hostname ์ถ์ถํ๊ณ , 
	- python ๋ผ์ด๋ธ๋ฌ๋ฆฌ - urllib.parse
2. ์๋ฒ์ ์ฐ๊ฒฐ : socket ๋ง๋ค๊ธฐ
	- Socket has
		1)  address family(AF) ๊ฐ ์์. ์ด๋ป๊ฒ ๋ค๋ฅธ ์ปด์ ์ฐพ๋์ง ์๋ฆฌ๋ ๊ฒ.
			- ex) AF_INET, AF_BLUETOOTH
		2) type๋ ์์. SOCK ์ผ๋ก ์์
			- ex) SOCK_STREAM : ์์์ ๋ฐ์ดํฐ ์ฌ์ด์ฆ, SOCK_DGRAM : ์๋ก ๊ณ ์  ์ฌ์ด์ฆ ํจํท ์ ์ก
		3) protocol : ๋ ์ปดํจํฐ๊ฐ ์๋ก ์ฐ๊ฒฐ์ ๋งบ๋ ๊ณผ์ ์ ์ค๋ช. 
			- ex) IPPROTO_TCP.... ์์ฆ์ TCP๋ฅผ ์ ์ฐ๋ ๋ธ๋ผ์ฐ์ ๋ ์๋ค๊ณ . ํฌ๋กฌ์ QUIC ํ๋กํ ์ฝ์ ์ด๋ค.
```python
import socket
s = socket.socket(
	family=socket.AF_INET,
	type=socket.SOCK_STREAM,
	proto=socket.IPPROTO_TCP
)
// ์์ผ ์์ฑํ์ผ๋ฉด, ์ฐ๊ฒฐ์ ํด์ผํจ. (host, port) -- AF_INET ๋ฐฉ์
s.connect((host, 80))  

// s => <socket.socket fd=3, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=6, laddr=('192.168.1.2', 58114), raddr=('93.184.216.34', 80)>

```

3.  request  
- ์ฒซ ์งธ์ค : GET - method, path - resource, HTTP/1.0 - protocol version
- ๋ ์งธ์ค (header): Host: host ~~
```python
s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") + 
       "Host: {}\r\n\r\n".format(host).encode("utf8"))

// return ๊ฐ 46 - ๋ค๋ฅธ ์ปด์ผ๋ก ๋ณด๋ธ bytes
```
\r\n ํด์ผ ๋น ์นธ ๋ค์ด๊ฐ๊ณ , ์ ๋๋ก ๋๋ค๊ณ ...

4. response
```python
response = s.makefile("r", encoding="utf8", newline="\r\n")

// return <_io.TextIOWrapper name=3 mode='r' encoding='utf8'>

statusline = response.readline()
version, status, explanation = statusline.split(" ", 2)
'HTTP/1.0 400 Bad Request\r\n' -- ๋ด ์ชฝ์์  ํ๋ก์ ์ค์  ๋๋ฌธ์ธ์ง 200 ์๋.
```

- ๋๋จธ์ง๋ ํค๋ ์ ๋ฐ๋
~~~python
headers = {}
while True:
	line = response.readline()
	if line == "\r\n": break
	header, value = line.split(":", 1)

body = response.read()

// ๋ซ๊ธฐ
s.close()
~~~

## Displaying the HTML
- response ์ body๊ฐ ๋ธ๋ผ์ฐ์ ์ ๋ฟ๋ ค์ฃผ๋ content๋ฅผ ๊ฒฐ์ 
 

- ์์๊บผ ๋ค ํฉ์ณ์, ์คํํ๋ฉด body ํ์คํธ ๋ณด์ฌ์ฃผ๋ ํ์ด์ฌ ์คํ๋ฌธ ๋ง๋ค ์ ์์.

## Encrypted connections == HTTPS
- https!!!
	- http over TLS
	- http ์ ์ ๋ถ ๋์ผ. except ํธ์คํธ์ ๋ธ๋ผ์ฐ์  ์ฌ์ด์ ํต์ ์ด ์ ๋ถ ์ํธํ๋์๋ค๋ ๊ฒ.

- https ๊ตฌํ : ์ด๊ฒ์ ๊ฒ ๋ณต์กํ๋ฐ python ๋ผ์ด๋ธ๋ฌ๋ฆฌ ssl ๋ก ๊ฐ๋จํ๊ฒ.
 
```python
import ssl
ctx = ssl.create_default_context()
s = ctx.wrap_socket(s, server_hostname=host) # new socket
```


-- ์ฐ์ต์ผ๋ก ๋ ํ  ๊ฒ๋ค ์์ง๋ง,,, ํจ์ค

[[ch 2. Drawing to the Screen]]
