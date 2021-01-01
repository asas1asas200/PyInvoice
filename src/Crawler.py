import requests
from bs4 import BeautifulSoup
from time import time
from threading import Thread
from queue import Queue
from collections import namedtuple, Counter
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
			date = soup.find('a', {'data-toggle': 'tab'}).text[:-15]
			thousand = []
			two_hundred = []
			for html_id, price in (('fbonly', thousand), ('fbonly_200', two_hundred)): # 1000W and 200W
				for invoice in soup.find(id=html_id).select('tr')[1:]:
					com, addr, items = [i.text for i in invoice.select('td')[-3:]]
					addr = addr[:3]
					if addr == '台北市':
						addr = '臺北市'
					elif addr == '桃園縣':
						addr = '桃園市'
					price.append(self.Invoice(com, addr, items))

			q.put({date: {'thousand': thousand, 'two_hundred': two_hundred}})
			
		self.home = 'https://www.etax.nat.gov.tw/'
		soup = parse_page('https://www.etax.nat.gov.tw/etw-main/web/ETW183W1/')
		lst = soup.find_all('td', {'headers': 'title'})[:-8:2]
		q = Queue()
		threads = []
		for i in lst:
			t = Thread(target=get_invoices, args=(self.home + i.find('a')['href'], q))
			t.start()
			threads.append(t)
		for i in threads:
			i.join()
		self.invoices = {}
		while q.qsize():
			self.invoices.update(q.get())

	@property
	def dates(self):
		return sorted(self.invoices.keys(), reverse=True)

	@property
	def addrs(self):
		ret = []
		for i in self.invoices.values():
			for price in ('thousand', 'two_hundred'):
				for j in i[price]:
					ret.append(j.addr)
		return sorted(ret)
	
if __name__ == '__main__':
	crawler = Crawler()
	print(Counter(crawler.addrs))
