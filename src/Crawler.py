import requests
from bs4 import BeautifulSoup
from time import time
from threading import Thread
from queue import Queue
from collections import namedtuple, Counter
import re
class Crawler:
	def __init__(self):
		self.Invoice = namedtuple('Invoice', ['com', 'addr', 'items', 'spent'])
		def parse_page(url):
			r = requests.get(url)
			r.encoding = 'utf-8'
			soup = BeautifulSoup(r.text, 'html.parser')
			return soup
		def get_invoices(url, q):
			def parse_addr(addr):
				addr = addr[:3]
				if addr == '台北市':
					addr = '臺北市'
				elif addr == '桃園縣':
					addr = '桃園市'
				return addr

			def parse_items(items):
				items = re.sub(r'[ ,]', '', items)
				match = re.search(r'[共計]?(\d*)元', items)
				if match:
					spent = int(match[1])
					items = re.sub(match[0], '', items)
				else:
					spent = -1
				items = re.sub(r'\d+[杯瓶罐項]', '', items)
				items = re.sub(r'\*\d*', '', items)
				items = re.sub(r'[共計等，。]', '', items)
				items = re.split(r'、|及', items)
				return items, spent

			soup = parse_page(url)
			date = soup.find('a', {'data-toggle': 'tab'}).text[:-15]
			thousand = []
			two_hundred = []
			for html_id, price in (('fbonly', thousand), ('fbonly_200', two_hundred)): # 1000W and 200W
				for invoice in soup.find(id=html_id).select('tr')[1:]:
					com, addr, items = [i.text for i in invoice.select('td')[-3:]]
					addr = parse_addr(addr)
					items, spent = parse_items(items)
					price.append(self.Invoice(com, addr, items, spent))

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

	def get_date_range_info(self, start, end):
		dates = list(reversed(self.dates))
		now = dates.index(start)
		thousand = []
		two_hundred = []
		while True:
			thousand.append(self.invoices[dates[now]]['thousand'])
			two_hundred.append(self.invoices[dates[now]]['two_hundred'])
			if dates[now] == end:
				break
			now += 1
		return thousand, two_hundred

	@property
	def dates(self):
		return sorted(self.invoices.keys(), reverse=True)

	def __get_property(self, attr):
		ret = []
		for i in self.invoices.values():
			for price in ('thousand', 'two_hundred'):
				for j in i[price]:
					ret.append(getattr(j, attr))
		return sorted(ret)
	@property
	def spents(self):
		return self.__get_property('spent')

	@property
	def items(self):
		return self.__get_property('items')

	@property
	def addrs(self):
		return self.__get_property('addr')

if __name__ == '__main__':
	crawler = Crawler()
	with open('items.txt', 'w') as file:
		file.write('\n'.join(map(str,crawler.items)))
		
