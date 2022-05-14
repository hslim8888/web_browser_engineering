---
created: 2022-05-07 01:25
tag:
- 🧑🏻‍💻 공부
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

- 브라우저를 쓰면 처음 하는 게 url을 통해 1) 연결, 서버로부터 정보를 2) 다운로드

## 1) Connection to a server
- DNS > ip .. 라우터 등등을 통해 서버에 연결
![[urls.png]]
![[connecting to a host.png]]

## 2) Requesting information
![[http requests 1.png]]

### Method, Resource, Protocol(http) Version
- 첫 번째 라인
- http version엔 0.9, 1.0, 1.1, 2.0 이 있는데 1.1이 스탠다드, 2.0은 복잡한 웹 앱만 가능. 브라우저는 소화하기 힘든 듯?

### Headers
- header 
	- key: value 로 구성
	- 기본적으로 Host, User-Agent 등 이 있음. 

### Body
- Additional request content

## 3) Server's response
![[resposne.png]]
![[status code.png]]

response도 request와 마찬가지로 3 파트로 구성
### Protoco Version, Status Code, Explanation
### Headers
### Body

## <실습> Telent in Python
1. url 에서 hostname 추출하고, 
	- python 라이브러리 - urllib.parse
2. 서버에 연결 : socket 만들기
	- Socket has
		1)  address family(AF) 가 있음. 어떻게 다른 컴을 찾는지 알리는 것.
			- ex) AF_INET, AF_BLUETOOTH
		2) type도 있음. SOCK 으로 시작
			- ex) SOCK_STREAM : 임의의 데이터 사이즈, SOCK_DGRAM : 서로 고정 사이즈 패킷 전송
		3) protocol : 두 컴퓨터가 서로 연결을 맺는 과정을 설명. 
			- ex) IPPROTO_TCP.... 요즘은 TCP를 안 쓰는 브라우저도 있다고. 크롬은 QUIC 프로토콜은 쓴다.
```python
import socket
s = socket.socket(
	family=socket.AF_INET,
	type=socket.SOCK_STREAM,
	proto=socket.IPPROTO_TCP
)
// 소켓 생성했으면, 연결을 해야함. (host, port) -- AF_INET 방식
s.connect((host, 80))  

// s => <socket.socket fd=3, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=6, laddr=('192.168.1.2', 58114), raddr=('93.184.216.34', 80)>

```

3.  request  
- 첫 째줄 : GET - method, path - resource, HTTP/1.0 - protocol version
- 둘 째줄 (header): Host: host ~~
```python
s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8") + 
       "Host: {}\r\n\r\n".format(host).encode("utf8"))

// return 값 46 - 다른 컴으로 보낸 bytes
```
\r\n 해야 빈 칸 들어가고, 제대로 된다고...

4. response
```python
response = s.makefile("r", encoding="utf8", newline="\r\n")

// return <_io.TextIOWrapper name=3 mode='r' encoding='utf8'>

statusline = response.readline()
version, status, explanation = statusline.split(" ", 2)
'HTTP/1.0 400 Bad Request\r\n' -- 내 쪽에선 프록시 설정 때문인지 200 아님.
```

- 나머지는 헤더 와 바디
~~~python
headers = {}
while True:
	line = response.readline()
	if line == "\r\n": break
	header, value = line.split(":", 1)

body = response.read()

// 닫기
s.close()
~~~

## Displaying the HTML
- response 의 body가 브라우저에 뿌려주는 content를 결정
 

- 위에꺼 다 합쳐서, 실행하면 body 텍스트 보여주는 파이썬 실행문 만들 수 있음.

## Encrypted connections == HTTPS
- https!!!
	- http over TLS
	- http 와 전부 동일. except 호스트와 브라우저 사이의 통신이 전부 암호화되었다는 것.

- https 구현 : 이것저것 복잡한데 python 라이브러리 ssl 로 간단하게.
 
```python
import ssl
ctx = ssl.create_default_context()
s = ctx.wrap_socket(s, server_hostname=host) # new socket
```


-- 연습으로 더 할 것들 있지만,,, 패스

[[ch 2. Drawing to the Screen]]
