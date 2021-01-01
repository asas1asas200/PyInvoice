import requests
from bs4 import BeautifulSoup
from time import time
from threading import Thread
from queue import Queue
from collections import namedtuple
class Crawler:
	def __init__(self):
		self.Invoice = namedtuple('Invoice', ['com', 'addr', 'items'])
		def parse_page(url):
			r = requests.get(url)
			r.encoding = 'utf-8'
			soup = BeautifulSoup(r.text, 'html.parser')
			return soup
		def get_invoices(url, q):
			soup = parse_page(url)
			thousand = [ self.Invoice(*[ j.text for j in i.select('td')[-3:] ])
				for i in soup.find(id='fbonly').select('tr')[1:] ]
			two_hundred = [ self.Invoice(*[ j.text for j in i.select('td')[-3:] ])
				for i in soup.find(id='fbonly_200').select('tr')[1:] ]
			q.put((thousand, two_hundred))
			
		self.home = 'https://www.etax.nat.gov.tw/'
		soup = parse_page('https://www.etax.nat.gov.tw/etw-main/web/ETW183W1/')
		lst = soup.find_all('td', {'headers': 'title'})[:-8:2]
		s = time()
		q = Queue()
		threads = []
		for i in lst:
			t = Thread(target=get_invoices, args=(self.home + i.find('a')['href'], q))
			t.start()
			threads.append(t)
		for i in threads:
			i.join()
		res = []
		while q.qsize():
			print(q.get())
#			r = requests.get(self.home + i.find('a')['href'])
#			r.encoding = 'utf-8'
#			print(r.text)
		print(time() - s)
	
if __name__ == '__main__':
	crawler = Crawler()
	
		
