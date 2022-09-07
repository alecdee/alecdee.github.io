#!/usr/bin/python3

from http.server import HTTPServer,SimpleHTTPRequestHandler,test
import sys
class CORSRequestHandler(SimpleHTTPRequestHandler):
	def end_headers(self):
		self.send_header("Access-Control-Allow-Origin","*")
		SimpleHTTPRequestHandler.end_headers(self)
if __name__=="__main__":
	port=int(sys.argv[1]) if len(sys.argv)>1 else 8000
	print("http://localhost:"+str(port))
	test(CORSRequestHandler,HTTPServer,port=port)
